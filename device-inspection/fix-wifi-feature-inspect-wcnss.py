from pathlib import Path
r=Path('/home/pablo/kyf37-android10');d=r/'device/kyocera/kyf37';s=(d/'device.mk').read_text()
for f in ['android.hardware.wifi.xml','android.hardware.wifi.direct.xml']:
 mapping='frameworks/native/data/etc/'+f+':system/etc/permissions/'+f
 if mapping not in s:s+='\nPRODUCT_COPY_FILES += '+mapping+'\n'
(d/'device.mk').write_text(s)
for p in (d/'ramdisk').glob('*.rc'):
 lines=p.read_text().splitlines()
 for i,l in enumerate(lines):
  if any(x in l.lower() for x in ['wcnss','cnss','wlan','wifi']):print(p.name,i+1,'\n'.join(lines[max(0,i-2):i+6]))
stock=Path('/home/pablo/kyf37-rom/stock-system')
for p in stock.rglob('*'):
 if p.is_file() and any(x in p.name.lower() for x in ['wcnss','cnss','wlan']):print(p.relative_to(stock))
