from pathlib import Path
import json
root=Path('/home/pablo/kyf37-rom/afphome-port-smali')
source=Path('/home/pablo/kyf37-rom/vendor-framework-smali/jp/kyocera/kcfp/util/KCfpSharedResources.smali')
old='Ljp/kyocera/kcfp/util/KCfpSharedResources;'
new='Lorg/kyf37/compat/SharedResources;'
for p in root.rglob('*.smali'):
 s=p.read_text()
 if old in s:p.write_text(s.replace(old,new))
p=root/'org/kyf37/compat/SharedResources.smali'
p.write_text(source.read_text().replace(old,new))
maps={'mResName':{},'mResType':{}};current=None;key=value=None
for line in source.read_text().splitlines():
 if 'sget-object v0,' in line:
  current=next((k for k in maps if '->'+k+':' in line),None)
  key=value=None
 elif current and 'const-string v1,' in line:key=line.split('"')[1]
 elif current and 'const-string v2,' in line:value=line.split('"')[1]
 elif current and '->put(' in line:
  assert key is not None and value is not None
  maps[current][key]=value;current=None
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
(host/'afphome-shared-resource-map.json').write_text(json.dumps({
 'aliases':maps,'note':'Original helper behavior retained app-locally. All referenced Android resource names must be ported/verified; copying helper alone is not sufficient.'},indent=2))
print('Copied original resource helper app-locally; mapped',len(maps['mResName']),'resource aliases')
