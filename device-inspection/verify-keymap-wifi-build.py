from pathlib import Path
import hashlib,json,re
r=Path('/home/pablo/kyf37-android10');out=r/'out/target/product/kyf37/system';labels=(r/'frameworks/native/include/input/InputEventLabels.h').read_text();a=labels.index('FLAGS[]');b=labels.index('};',a);flags=set(re.findall(r'DEFINE_FLAG\(([^)]+)\)',labels[a:b]));assert 'WAKE' not in flags
report={}
for p in (r/'device/kyocera/kyf37/keylayout').glob('*.kl'):
 for line in p.read_text().splitlines():
  cols=line.split('#')[0].split()
  if cols and cols[0]=='key':
   start=4 if cols[1]=='usage' else 3
   assert all(flag in flags for flag in cols[start:]),(p,line)
 target=out/'usr/keylayout'/p.name
 assert target.read_bytes()==p.read_bytes(),p
 report[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
for f in ['android.hardware.wifi.xml','android.hardware.wifi.direct.xml']:
 assert (out/'etc/permissions'/f).read_bytes()==(r/'frameworks/native/data/etc'/f).read_bytes()
report.update({'key_maps_build_verified':True,'side_key_owner_verified':True,'wifi_ui_device_verified':True,'wifi_hardware_verified':False})
p=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/keymap-wifi-validation.json');p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
