from pathlib import Path
r=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
for p in r.rglob('*.rc'):
 s=p.read_text()
 if any(x in s for x in ['kyf37','wcnss-service']):
  print(p)
  for i,l in enumerate(s.splitlines()):
   if 'wcnss' in l or 'kyf37' in l:print(i,l)
