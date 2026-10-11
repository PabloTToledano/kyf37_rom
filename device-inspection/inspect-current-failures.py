from pathlib import Path
r=Path('/home/pablo/kyf37-rom/irda-port-smali')
for p in r.rglob('*.smali'):
 s=p.read_text()
 if 'Lcom/kyocera/mdm/' in s:
  print('\nFILE',p)
  lines=s.splitlines()
  hits=[i for i,l in enumerate(lines) if 'Lcom/kyocera/mdm/' in l or 'mdm' in l.lower()]
  for i in hits:
   print('\n'.join(lines[max(0,i-3):i+5]))
root=Path('/home/pablo/kyf37-android10/packages/apps/Kyf37OuterScreen')
for f in ['controller.c','framebuffer.c']:
 print('\nFILE',f);print((root/f).read_text())
