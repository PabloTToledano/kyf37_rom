from pathlib import Path
import re
root=Path('/home/pablo/kyf37-android10')
p=root/'device/kyocera/kyf37/ramdisk/init.qcom.rc';s=p.read_text()
remove=['mkdir /mnt/shell/emulated','mkdir /storage/emulated','export EMULATED_STORAGE_SOURCE','export EMULATED_STORAGE_TARGET','export SECONDARY_STORAGE','export EXTERNAL_STORAGE','symlink /storage/emulated/legacy','symlink /mnt/shell/emulated/0']
s='\n'.join(line for line in s.splitlines() if not any(line.strip().startswith(x) for x in remove))+'\n'
s=re.sub(r'^service (?:sdcard|fuse_sdcard1|fuse_uicc0|fuse_uicc1|fuse_usbotg) .*?(?=^\S|\Z)','',s,flags=re.M|re.S)
s=re.sub(r'^on property:init.svc.sdcard=running\n(?:[ \t].*\n|\n)*','',s,flags=re.M)
assert 'export EMULATED_STORAGE_TARGET' not in s and 'service sdcard ' not in s
p.write_text(s)
# This ramdisk-only correction is copied into the packaging inputs; system unchanged.
(root/'out/target/product/kyf37/root/init.qcom.rc').write_text(s)
print('Legacy storage exports/services removed; Android10 init/vold owns storage')
