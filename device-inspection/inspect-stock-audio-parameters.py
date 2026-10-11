from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port/backend-reference')
for folder in ['Telecom','TeleService']:
 for p in (r/folder).rglob('*.smali'):
  lines=p.read_text().splitlines()
  for i,l in enumerate(lines):
   if 'const-string' in l and any(k in l.lower() for k in ['hear','memo','rxvoice','mute','answerhold']):
    if any(k in l.lower() for k in ['param','effect','record','rxvoice','play','answerhold','hearing']):print(str(p.relative_to(r))+': '+l.strip())
