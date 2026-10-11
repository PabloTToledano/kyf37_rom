"""Stage recovered OEM resources as named Android framework additions (WSL)."""
from pathlib import Path
import shutil,xml.etree.ElementTree as ET
ws=Path(__file__).resolve().parent.parent;source=ws/'kyf37-rom/all-stock-app-ports/resource-decoded/res'
if not source.is_dir():raise RuntimeError('Extract/decode original resources first')
dest=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/overlay/frameworks/base/core/res/res')
for asset in source.rglob('*'):
 if not asset.is_file():continue
 target=dest/asset.relative_to(source)
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists() or target.read_bytes()!=asset.read_bytes():shutil.copy2(asset,target)
root=ET.Element('resources');added=set()
for asset in source.rglob('*'):
 if not asset.is_file():continue
 kind=asset.parent.name.split('-')[0]
 if kind=='values':
  for entry in ET.parse(asset).getroot():
   kindName={'integer-array':'array','string-array':'array'}.get(entry.tag,entry.tag)
   if entry.get('name'):added.add((kindName,entry.get('name')))
 else:added.add((kind,asset.name.split('.')[0]))
for kind,name in sorted(added):ET.SubElement(root,'add-resource',{'type':kind,'name':name})
target=dest/'values/kyf37_remaining_stock_additions.xml'
content=ET.tostring(root,encoding='utf-8',xml_declaration=True)
if not target.exists() or target.read_bytes()!=content:target.write_bytes(content)
print('Staged',len(added),'named OEM framework resources; rebuild framework-res then reconstruct candidate APKs')
