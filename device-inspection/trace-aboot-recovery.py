from pathlib import Path
import json,struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
p=Path(__file__).resolve().parent
raw=(p.parent/'phone-backup/kyf37-root-backup/aboot.img').read_bytes()
base=0x8f600000
off=0x8000
d=Cs(CS_ARCH_ARM,CS_MODE_ARM);d.skipdata=True
ins=list(d.disasm(raw[off:off+375352],base))
targets={}
for text in [b'Failed to write protect dev info',b'FOTA : write protect clr',b'kcpermissive',b'ERROR: Could not do normal boot.',b'error in emmc_recovery_init',b'fastboot',b'Need wipe userdata',b'oem unlock is not allowed']:
    n=0
    while True:
        n=raw.find(text,n)
        if n<0: break
        if off<=n<off+375352:targets[base+n-off]=text.decode()
        n+=1
low={};out=[]
for i,x in enumerate(ins):
    args=x.op_str.split(', ')
    if x.mnemonic.startswith('movw') and len(args)==2 and args[1].startswith('#'):
        low[args[0]]=(int(args[1][1:],0),i)
    elif x.mnemonic.startswith('movt') and len(args)==2 and args[0] in low:
        v,j=low[args[0]]
        v|=int(args[1][1:],0)<<16
        if v in targets and x.address-ins[j].address<=32:
            out.append('\nSTRING '+targets[v]+' @ '+hex(v)+'\n')
            out += [f'{a.address:#x} {a.mnemonic} {a.op_str}\n' for a in ins[max(0,j-25):i+35]]
(p/'aboot-recovery-route-traces.txt').write_text(''.join(out))
print(''.join(out))
