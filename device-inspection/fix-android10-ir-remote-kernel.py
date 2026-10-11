"""Stage experimental GPIO consumer IR ioctl; no build, staging or phone access."""
from pathlib import Path
import shutil
ws=Path(__file__).resolve().parent
k=Path.home()/'kyf37-rom/kernel-android10'
dst=k/'drivers/tty/serial'
for name in ('kyf37_ir_kernel.inc','kyf37_ir_uapi.h'):
    shutil.copy2(ws/'ir-remote'/name,dst/name)
p=dst/'msm_serial_hs_lite.c';s=p.read_text()
marker='#include "kyf37_ir_kernel.inc"'
old_probe='''        return uport->mapbase == 0x078b0000 && msm_hsl_port->use_pinctrl &&
            !IS_ERR(pinctrl_lookup_state(msm_hsl_port->pinctrl, "kyf37_ir_tx")) ? 0 : -ENODEV;'''
new_probe='''        return uport->mapbase == 0x078b0000 && msm_hsl_port->use_pinctrl &&
            !IS_ERR_OR_NULL(msm_hsl_port->gpio_state_inactive) &&
            gpio_is_valid(kyf37_ir_gpio()) ? 0 : -ENODEV;'''
if old_probe in s:s=s.replace(old_probe,new_probe);p.write_text(s)
if marker not in s:
    anchor='static int msm_hsl_ioctl(struct uart_port *uport, unsigned int cmd,'
    assert s.count(anchor)==1
    s=s.replace(anchor,marker+'\n\n'+anchor)
    anchor='    switch(cmd){\n    case TIOCSERIROFF:'
    assert s.count(anchor)==1
    s=s.replace(anchor,'''    switch(cmd){
    case KYF37_IR_PROBE:
        if (!capable(CAP_SYS_RAWIO)) return -EPERM;
        return uport->mapbase == 0x078b0000 && msm_hsl_port->use_pinctrl &&
            !IS_ERR_OR_NULL(msm_hsl_port->gpio_state_inactive) &&
            gpio_is_valid(kyf37_ir_gpio()) ? 0 : -ENODEV;
    case KYF37_IR_SEND:
        return kyf37_ir_send(uport, arg);
    case TIOCSERIROFF:''')
    p.write_text(s)
# Remove only this experiment's earlier DTS additions. Existing OEM QCDT already
# has a GPIO inactive state; using it avoids changing the verified boot DT image.
p=k/'arch/arm/boot/dts/qcom/msm8909.dtsi';s=p.read_text()
old='''kc,remote-tx = <&msm_gpio 20 0>;
        pinctrl-names = "uart3_inactive", "uart3_active", "uart3_sleep", "kyf37_ir_tx";
        pinctrl-3 = <&kyf37_ir_tx_gpio>;'''
if old in s:p.write_text(s.replace(old,'pinctrl-names = "uart3_inactive", "uart3_active", "uart3_sleep";'))
p=k/'arch/arm/boot/dts/qcom/msm8909-pinctrl.dtsi';s=p.read_text()
old='''            kyf37_ir_tx_gpio: kyf37_ir_tx_gpio {
                drive-strength = <2>;
                output-low;
                bias-disable;
            };
'''
if old in s:p.write_text(s.replace(old,''))
print('Consumer IR kernel source staged; GPIO optical response UNVERIFIED; no phone operations')
