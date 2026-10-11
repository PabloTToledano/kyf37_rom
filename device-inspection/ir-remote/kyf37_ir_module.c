/* GPL-2.0-only. Reversible consumer IR module for the existing KYF37 kernel. */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/serial_core.h>
#include <linux/tty.h>
#include <linux/gpio.h>
#include <linux/pinctrl/consumer.h>
#include <linux/miscdevice.h>
#include <linux/fs.h>
#include <linux/delay.h>
#include <linux/ktime.h>
static struct device *ir_device;
static struct uart_port *ir_port;
static struct pinctrl *ir_pinctrl;
static struct pinctrl_state *ir_inactive, *ir_active;
static unsigned long sent_count, failed_count;
static unsigned int last_frequency, last_count;
module_param_named(sent, sent_count, ulong, 0444);
module_param_named(failed, failed_count, ulong, 0444);
module_param(last_frequency, uint, 0444);
module_param(last_count, uint, 0444);
#include "kyf37_ir_module_emit.inc"
module_param(ir_late_ns, ulong, 0444);
module_param(ir_fail_stage, ulong, 0444);
module_param(ir_fail_index, ulong, 0444);
static long ir_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
 int ret;
 (void)file;
 if (!capable(CAP_SYS_RAWIO)) return -EPERM;
 if (!ir_port || !ir_port->state || !ir_port->ops) return -ENODEV;
 if (cmd==KYF37_IR_PROBE) return gpio_is_valid(kyf37_ir_gpio()) ? 0 : -ENODEV;
 if (cmd!=KYF37_IR_SEND) return -ENOTTY;
 ret=mutex_lock_interruptible(&ir_port->state->port.mutex);
 if (ret) return ret;
 ret=kyf37_ir_send(ir_port,arg);
 if (!ret) ++sent_count; else ++failed_count;
 mutex_unlock(&ir_port->state->port.mutex);
 return ret;
}
static const struct file_operations ir_fops={
 .owner=THIS_MODULE,.unlocked_ioctl=ir_ioctl,
};
static struct miscdevice ir_misc={.minor=MISC_DYNAMIC_MINOR,.name="kyf37_ir",.fops=&ir_fops,.mode=0600};
static int __init ir_init(void)
{
 int ret;
 ir_device=bus_find_device_by_name(&platform_bus_type,NULL,"78b0000.serial");
 if (!ir_device) return -ENODEV;
 ir_port=dev_get_drvdata(ir_device);
 if (!ir_port || ir_port->mapbase!=0x078b0000) { ret=-ENODEV; goto device; }
 ir_pinctrl=pinctrl_get(ir_device);
 if (IS_ERR(ir_pinctrl)) { ret=PTR_ERR(ir_pinctrl); goto device; }
 ir_inactive=pinctrl_lookup_state(ir_pinctrl,"uart3_inactive");
 ir_active=pinctrl_lookup_state(ir_pinctrl,"uart3_active");
 if (IS_ERR(ir_inactive)||IS_ERR(ir_active)||!gpio_is_valid(kyf37_ir_gpio())) { ret=-ENODEV; goto pins; }
 ret=misc_register(&ir_misc);
 if (!ret) { pr_info("kyf37_ir: registered bounded GPIO TX, stock UART/DT unchanged\n"); return 0; }
pins: pinctrl_put(ir_pinctrl);
device: put_device(ir_device); return ret;
}
static void __exit ir_exit(void)
{
 misc_deregister(&ir_misc);pinctrl_put(ir_pinctrl);put_device(ir_device);
}
module_init(ir_init);module_exit(ir_exit);
MODULE_LICENSE("GPL");MODULE_DESCRIPTION("KYF37 bounded consumer infrared transmitter");
