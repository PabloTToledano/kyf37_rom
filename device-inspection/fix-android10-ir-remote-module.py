"""Generate an external module using the same bounded emitter as the UART patch."""
from pathlib import Path
import shutil
ws=Path(__file__).resolve().parent
src=ws/'ir-remote';out=Path.home()/'kyf37-rom/ir-remote-module';out.mkdir(exist_ok=True)
s=(src/'kyf37_ir_kernel.inc').read_text()
s=s.replace('msm_hsl_port/regmap', 'UART port/register')
s=s.replace(' struct msm_hsl_port *msm = UART_TO_MSM(port);\n','')
s=s.replace('unsigned int i, old_ir;','unsigned int i;')
s=s.replace('!msm->use_pinctrl','!ir_pinctrl')
s=s.replace('!msm_hsl_tx_empty(port)','!port->ops->tx_empty(port)')
s=s.replace('msm->gpio_state_inactive','ir_inactive').replace('msm->gpio_state_active','ir_active').replace('msm->pinctrl','ir_pinctrl')
s='\n'.join(x for x in s.splitlines() if not x.strip().startswith(('old_ir = msm_hsl_read','msm_hsl_write(port, old_ir')))+'\n'
s=s.replace(' active = !(r->flags & 1);',' last_frequency=r->frequency; last_count=r->count;\n active = !(r->flags & 1);')
assert 'msm_hsl_' not in s and 'UART_TO_MSM' not in s
(out/'kyf37_ir_module_emit.inc').write_text(s)
for n in ('kyf37_ir_module.c','kyf37_ir_uapi.h'):shutil.copy2(src/n,out/n)
(out/'Makefile').write_text('obj-m += kyf37_ir_module.o\n')
print('External module staged; build against CURRENT kernel ABI before loading; no device access')
