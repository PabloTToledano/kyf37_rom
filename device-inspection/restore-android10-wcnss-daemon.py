from pathlib import Path
r=Path('/home/pablo/kyf37-android10');p=r/'device/kyocera/kyf37/ramdisk/ueventd.qcom.rc';s=p.read_text()
if 'firmware_directories /system/etc/firmware' not in s:s+='\nfirmware_directories /system/etc/firmware /firmware/image\n';p.write_text(s)
p=r/'device/kyocera/kyf37/device.mk';s=p.read_text();f='bin/wcnss_service';mk=r/'vendor/kyocera/kyf37/kyf37-vendor.mk';m=mk.read_text();mapping='vendor/kyocera/kyf37/proprietary/'+f+':system/'+f
import shutil
shutil.copy2('/home/pablo/kyf37-rom/stock-system/'+f,r/'vendor/kyocera/kyf37/proprietary'/f)
if mapping not in m:m+='\nPRODUCT_COPY_FILES += '+mapping+'\n';mk.write_text(m)
p=r/'vendor/kyocera/kyf37/proprietary-files.txt';s=p.read_text()
if f not in s.splitlines():s+=f+'\n';p.write_text(s)
print('Original WCNSS daemon restored; explicit legacy firmware search directories added')
