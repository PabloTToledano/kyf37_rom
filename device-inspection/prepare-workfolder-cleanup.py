from pathlib import Path
import json,re,zipfile,hashlib
r=Path.cwd();items=[];checks=[]
def digest(stream):
 h=hashlib.sha256()
 while True:
  b=stream.read(8*1024*1024)
  if not b:return h.hexdigest()
  h.update(b)
def add(p,reason):items.append({'path':str(p.relative_to(r)),'bytes':p.stat().st_size,'reason':reason})
for d in sorted((r/'kyf37-rom').glob('android10-go-candidate-20261007-v*')):
 m=re.fullmatch('android10-go-candidate-20261007-v(\d+)',d.name)
 if not m or int(m[1])>18:continue
 archive=r/'kyf37-rom'/('kyf37-android10-go-20261007-twrp-v'+m[1]+'.zip')
 if not archive.exists():continue
 with zipfile.ZipFile(archive) as z:
  manifest=json.loads(z.read('payload-manifest.json'));entry='system.raw.img'
  with z.open(entry) as f:actual=digest(f)
  assert actual==manifest[entry]['sha256'],archive
 raw=d/'system-android10.raw.img'
 if raw.exists():
  with raw.open('rb') as f:assert digest(f)==actual,raw
  add(raw,'Verified identical raw system retained inside installer ZIP')
 sparse=d/'system-android10.sparse.img'
 if sparse.exists():add(sparse,'Reproducible sparse encoding; verified raw payload retained in installer ZIP')
 checks.append({'archive':str(archive.relative_to(r)),'payload_sha256':actual})
 print('Verified retained installer v'+m[1],flush=True)
for d in (r/'kyf37-rom').glob('superseded-*'):
 for p in d.rglob('system-android10*.img'):add(p,'Explicitly superseded build-draft image; released versions retained')
 for p in d.glob('*.zip'):
  keep=r/'kyf37-rom'/p.name
  if keep.exists():
   with p.open('rb') as f:a=digest(f)
   with keep.open('rb') as f:b=digest(f)
   if a==b:add(p,'Byte-identical duplicate of retained root release ZIP')
inv=json.loads((r/'device-inspection/cleanup-inventory.json').read_text())
# File-only cache cleanup avoids recursive directory operations or reparse traversal.
for rel in inv['caches']:
 for p in (r/rel).rglob('*.pyc'):
  if p.is_file() and not p.is_symlink():add(p,'Regenerable Python bytecode cache')
plan={'root':str(r.resolve()),'files':items,'verified_archives':checks,'total_bytes':sum(x['bytes'] for x in items)}
(r/'device-inspection/cleanup-plan-20261011.json').write_text(json.dumps(plan,indent=2))
print('Planned',len(items),'files,',round(plan['total_bytes']/1024**3,2),'GiB',flush=True)
