from pathlib import Path
import json,re,hashlib
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom');stock=Path('/home/pablo/kyf37-rom/stock-system')
selected=set();links=[];missing=[]
for base in ['etc/firmware','lib/modules']:
 for p in (stock/base).rglob('*'):
  if p.is_symlink():links.append({'path':str(p.relative_to(stock)),'target':str(p.readlink())})
  elif p.is_file():selected.add(str(p.relative_to(stock)))
for pattern in ['audio*.conf','mixer_paths*.xml','sound_trigger*.xml','thermal*.conf','gps.conf','izat.conf','media_codecs.xml','media_profiles.xml','init.qcom*.sh']:
 for p in (stock/'etc').glob(pattern):
  if p.is_file():selected.add(str(p.relative_to(stock)))
for p in (host/'stock-boot-ramdisk').glob('*'):
 if p.suffix not in ['.rc','.sh']:continue
 for ref in re.findall(r'/system/[A-Za-z0-9_.+/-]+',p.read_text()):
  rel=ref[len('/system/'):];f=stock/rel
  if rel.startswith('etc/') and f.is_file():selected.add(rel)
  elif rel.endswith('.ko') and not f.exists():missing.append({'source':p.name,'path':ref})
items=[{'path':x,'bytes':(stock/x).stat().st_size,'sha256':hashlib.sha256((stock/x).read_bytes()).hexdigest()} for x in sorted(selected)]
(host/'hardware-support-files.json').write_text(json.dumps({'files':items,'symlinks':links,'missing_referenced_modules':missing,'note':'Selected model hardware support files. Keep modern Android software codec configs; review mixer/audio/media policy and init script compatibility before runtime.'},indent=2))
print('Hardware support files',len(items),'bytes',sum(x['bytes'] for x in items),'symlinks',len(links),'missing optional module references',len(missing))
