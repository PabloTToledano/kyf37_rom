from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10')
for p in r.rglob('*sub*.c'):
 if 'disp_ext' in str(p):
  print(p)
  s=p.read_text().splitlines()
  for i,l in enumerate(s):
   if any(x in l for x in ['blank','power','pan_display','0010','send_data']):print(str(i+1)+': '+l)
