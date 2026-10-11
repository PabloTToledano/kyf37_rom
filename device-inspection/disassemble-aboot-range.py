from pathlib import Path
import sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
p=Path(__file__).resolve().parent
b=(p.parent/'phone-backup/kyf37-root-backup/aboot.img').read_bytes()
a=int(sys.argv[1],0);n=int(sys.argv[2],0)
off=0x8000+a-0x8f600000
assert 0x8000<=off and off+n<=0x8000+375352
for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(b[off:off+n],a):
    print(f'{i.address:#x} {i.mnemonic} {i.op_str}')
