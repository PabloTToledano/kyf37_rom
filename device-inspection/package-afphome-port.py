"""Stage an unsigned offline APK, preserving all stock resources and manifest."""
import hashlib,json,zipfile
from pathlib import Path
root=Path('kyf37-rom')
original=root/'AfpHome-stock.apk'
dex=root/'AfpHome-softkey-port.dex'
output=root/'AfpHome-port-unsigned.apk'
assert dex.read_bytes()[:4]==b'dex\n'
preserved=[]
with zipfile.ZipFile(original) as source,zipfile.ZipFile(output,'w') as target:
 for entry in source.infolist():
  if entry.filename.startswith('META-INF/') or entry.filename=='classes.dex':continue
  data=source.read(entry)
  target.writestr(entry,data)
  preserved.append((entry.filename,hashlib.sha256(data).hexdigest()))
 target.writestr('classes.dex',dex.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(output) as check:
 for name,digest in preserved:assert hashlib.sha256(check.read(name)).hexdigest()==digest
 assert check.read('classes.dex')==dex.read_bytes()
report={'apk':output.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
 'preserved_manifest_and_resource_files':len(preserved),'signed':False,'installed':False,
 'warning':'Original compiled framework resource references and missing OEM providers still require adaptation. Not an install-ready or runtime-verified APK.'}
(root/'afphome-apk-staging.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
