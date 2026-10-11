from pathlib import Path
import re
r=Path('/home/pablo/kyf37-android10');host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/keylayouts-android10-valid');host.mkdir(exist_ok=True)
for p in (r/'device/kyocera/kyf37/keylayout').glob('*.kl'):
 s=re.sub(r'\s+WAKE(?:_DROPPED)?(?=\s|$)','',p.read_text());p.write_text(s.rstrip()+'\n');(host/p.name).write_bytes((s.rstrip()+'\n').encode())
print('Removed unsupported WAKE flags; Android10 physical wake remains handled by model policy')
