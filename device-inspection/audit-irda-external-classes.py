from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/irda-port-smali')
refs=set()
for p in r.rglob('*.smali'):
 for ref in re.findall(r'L(?:jp/kyocera|com/kyocera|com/kddi)/[^;]+;',p.read_text()):
  if not (r/(ref[1:-1]+'.smali')).exists():refs.add(ref)
print('\n'.join(sorted(refs)))
