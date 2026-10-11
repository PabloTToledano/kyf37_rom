from pathlib import Path
import shutil
root=Path('/home/pablo/kyf37-android10')
v=root/'vendor/kyocera/kyf37'
src=Path('/home/pablo/kyf37-rom/stock-system/bin/vm_bms')
dst=v/'proprietary/bin/vm_bms'
assert src.read_bytes()[:4]==b'\x7fELF'
shutil.copy2(src,dst)
p=v/'proprietary-files.txt'
s=p.read_text()
if 'bin/vm_bms' not in s.splitlines():p.write_text(s.rstrip()+'\nbin/vm_bms\n')
p=v/'kyf37-vendor.mk'
s=p.read_text()
line='PRODUCT_COPY_FILES += vendor/kyocera/kyf37/proprietary/bin/vm_bms:system/bin/vm_bms'
if line not in s:p.write_text(s.rstrip()+'\n'+line+'\n')
# Existing OEM init definition and /dev/vm_bms selection are retained.
print('Restored original fuel-gauge daemon to product; runtime validation pending')
