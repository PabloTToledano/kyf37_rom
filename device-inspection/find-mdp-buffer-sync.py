from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video')
for p in r.rglob('*'):
 if 'mdp3' in p.name:print(p)
for p in r.rglob('*.c'):
 if 'mdp' not in p.name:continue
 lines=p.read_text(errors='replace').splitlines()
 for i,l in enumerate(lines):
  if 'MSMFB_BUFFER_SYNC' in l:print(p,i+1,'\n'.join(lines[max(0,i-3):i+8]))
