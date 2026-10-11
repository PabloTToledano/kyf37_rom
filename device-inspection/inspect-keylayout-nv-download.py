from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
p=r/'frameworks/native/include/input/InputEventLabels.h';s=p.read_text();a=s.find('POLICY_FLAGS');print(s[a:a+1500]);print('\n'.join(l for l in s.splitlines() if 'WAKE' in l))
p=r/'frameworks/native/libs/input/KeyLayoutMap.cpp';s=p.read_text();a=s.find('parseKeyFlag');print(s[a:a+1200])
for p in (r/'device/kyocera/kyf37/keylayout').glob('*.kl'):
 print(p.name,repr(p.read_bytes()[-65:]))
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c');lines=p.read_text().splitlines()
for i,l in enumerate(lines):
 if 'request_firmware' in l or 'nv_downloaded =' in l:print(i+1,'\n'.join(lines[max(0,i-5):i+8]))
