from pathlib import Path
import shutil
root=Path('/home/pablo/kyf37-android10')
stock=Path('/home/pablo/kyf37-rom/stock-system')
files=sorted(p.relative_to(stock).as_posix() for p in (stock/'vendor/lib').glob('*ov8856*'))
files+=sorted(p.relative_to(stock).as_posix() for p in (stock/'vendor/lib').glob('libactuator_rohm_bu64243gwz*.so'))
p=root/'vendor/kyocera/kyf37/proprietary-files.txt'
s=p.read_text()
mk=root/'vendor/kyocera/kyf37/kyf37-vendor.mk'
m=mk.read_text()
for f in files:
 dst=root/'vendor/kyocera/kyf37/proprietary'/f
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stock/f,dst)
 if f not in s.splitlines():s+=f+'\n'
 mapping='vendor/kyocera/kyf37/proprietary/'+f+':system/'+f
 if mapping not in m:m+='\nPRODUCT_COPY_FILES += '+mapping+'\n'
p.write_text(s);mk.write_text(m)
print('Restored',len(files),'original OV8856 sensor/tuning/EEPROM/actuator libraries; audit required')
