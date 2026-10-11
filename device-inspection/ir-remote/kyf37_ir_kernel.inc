/* Experimental KYF37 consumer IR output through the existing TX pin.
 * Included after msm_hsl_port/regmap definitions. GPL-2.0-only.
 * Caller holds serial_core port mutex and kflcd hardware ownership.
 * IRQs are masked only during a bounded mark (maximum 10 ms), restored in spaces.
 */
#include <linux/capability.h>
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/math64.h>
#include <linux/sched.h>
#include "kyf37_ir_uapi.h"
static unsigned long ir_late_ns, ir_fail_stage, ir_fail_index;

static int kyf37_ir_chip_match(struct gpio_chip *chip, void *unused)
{
 (void)unused;
 return chip->label && !strcmp(chip->label, "msm_tlmm_gpio") && chip->ngpio > 20;
}

static int kyf37_ir_gpio(void)
{
 struct gpio_chip *chip = gpiochip_find(NULL, kyf37_ir_chip_match);
 return chip ? chip->base + 20 : -ENODEV;
}

static int kyf37_ir_send(struct uart_port *port, unsigned long arg)
{
 struct msm_hsl_port *msm = UART_TO_MSM(port);
 struct kyf37_ir_request *r;
 struct pinctrl_state *tx;
 u64 total = 0, period, on, start, stop, edge, now;
 unsigned int i, old_ir;
 int ret = 0, gpio, active;
 unsigned long irq_flags;
 if (!capable(CAP_SYS_RAWIO)) return -EPERM;
 if (port->mapbase != 0x078b0000 || !msm->use_pinctrl) return -ENODEV;
 if (port->suspended || !uart_circ_empty(&port->state->xmit) ||
     !msm_hsl_tx_empty(port)) return -EBUSY;
 gpio = kyf37_ir_gpio();
 if (!gpio_is_valid(gpio) || gpio_cansleep(gpio)) return -ENODEV;
 /* OEM uart3_inactive already muxes TX20/RX21 to GPIO; preserve stock QCDT. */
 tx = msm->gpio_state_inactive;
 if (IS_ERR_OR_NULL(tx)) return -ENODEV;
 r = kmalloc(sizeof(*r), GFP_KERNEL);
 if (!r) return -ENOMEM;
 if (copy_from_user(r, (void __user *)arg, sizeof(*r))) { ret=-EFAULT; goto free; }
 if (r->frequency < 30000 || r->frequency > 60000 || !r->count ||
     r->count > KYF37_IR_MAX || (r->flags & ~3U)) { ret=-EINVAL; goto free; }
 for (i=0; i<r->count; ++i) {
  if (signal_pending(current)) { ret=-EINTR; goto free; }
  if (!r->duration[i] || r->duration[i] > 100000 ||
      (!(i & 1) && r->duration[i] > 10000)) { ret=-EINVAL; goto free; }
  total += r->duration[i];
 }
 if (total > 400000) { ret=-EINVAL; goto free; }
 period = div_u64(1000000000ULL, r->frequency);
 ir_late_ns=0;ir_fail_stage=0;ir_fail_index=0;
 on = (r->flags & 2) ? 2000 : div_u64(period, 3);
 active = !(r->flags & 1);
 old_ir = msm_hsl_read(port, regmap[msm->ver_id][UARTDM_IRDA]);
 /* GPIO bypasses UART SIR pulse shaping, without changing its termios. */
 ret = pinctrl_select_state(msm->pinctrl, tx);
 if (ret) goto free;
 ret = gpio_direction_output(gpio, !active);
 if (ret) {
  pinctrl_select_state(msm->pinctrl, msm->gpio_state_active);
  goto free;
 }
 gpio_set_value(gpio, !active);
 for (i=0; i<r->count; ++i) {
  if (signal_pending(current)) { ret=-EINTR; break; }
  if (i & 1) {
   /* Give scheduler time in long spaces. Short spaces retain microsecond timing. */
   start = ktime_to_ns(ktime_get());
   if (r->duration[i] >= 10000)
    usleep_range(r->duration[i]-3000, r->duration[i]-2900);
   preempt_disable();
   while (ktime_to_ns(ktime_get()) < start + (u64)r->duration[i]*1000)cpu_relax();
   preempt_enable();
   now=ktime_to_ns(ktime_get());
   if (now > start + (u64)(r->duration[i]+200)*1000) {
    ir_late_ns=now-start-(u64)r->duration[i]*1000;ir_fail_stage=1;ir_fail_index=i;
    ret=-ETIME; break;
   }
   continue;
  }
  preempt_disable();
  local_irq_save(irq_flags);
  start = ktime_to_ns(ktime_get());
  stop = start + (u64)r->duration[i]*1000;
  edge = start;
  while (edge < stop) {
   now = ktime_to_ns(ktime_get());
   if (now > edge + 8000) { ir_late_ns=now-edge;ir_fail_stage=2;ir_fail_index=i;ret=-ETIME; break; }
   gpio_set_value(gpio, active);
   while (ktime_to_ns(ktime_get()) < min(edge+on,stop)) cpu_relax();
   gpio_set_value(gpio, !active);
   now = ktime_to_ns(ktime_get());
   if (now > edge+on+8000) { ir_late_ns=now-edge-on;ir_fail_stage=3;ir_fail_index=i;ret=-ETIME; break; }
   edge += period;
   while (ktime_to_ns(ktime_get()) < min(edge,stop)) cpu_relax();
  }
  gpio_set_value(gpio, !active);
  local_irq_restore(irq_flags);
  preempt_enable();
  if (ret) break;
 }
 gpio_set_value(gpio, !active);
 /* Always restore UART mux; shutdown gate is closed by the helper afterward. */
 if (pinctrl_select_state(msm->pinctrl, msm->gpio_state_active) && !ret) ret=-EIO;
 msm_hsl_write(port, old_ir, regmap[msm->ver_id][UARTDM_IRDA]);
free:
 kfree(r);
 return ret;
}
