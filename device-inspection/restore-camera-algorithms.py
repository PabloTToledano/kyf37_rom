from pathlib import Path
import shutil
root=Path('/home/pablo/kyf37-android10');stock=Path('/home/pablo/kyf37-rom/stock-system')
dsthost=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/camera-sensor-libs')
p=root/'vendor/kyocera/kyf37/proprietary-files.txt';s=p.read_text();mk=root/'vendor/kyocera/kyf37/kyf37-vendor.mk';m=mk.read_text()
for lib in (stock/'vendor/lib').glob('*.so'):
 if not any(x in lib.name for x in ['tintless','mmcamera2_stats','actuator_rohm']):continue
 f='vendor/lib/'+lib.name
 dst=root/'vendor/kyocera/kyf37/proprietary'/f;shutil.copy2(lib,dst);shutil.copy2(lib,dsthost/lib.name)
 if f not in s.splitlines():s+=f+'\n';print('Added',f)
 mapping='vendor/kyocera/kyf37/proprietary/'+f+':system/'+f
 if mapping not in m:m+='\nPRODUCT_COPY_FILES += '+mapping+'\n'
p.write_text(s);mk.write_text(m)
