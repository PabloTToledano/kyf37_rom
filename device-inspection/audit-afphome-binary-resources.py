"""Find stock framework IDs in compiled APK containers; candidates, not rewriting."""
import json,zipfile,struct
from pathlib import Path
from androguard.core.axml import ARSCParser
from loguru import logger
logger.remove()
root=Path('kyf37-rom')
with zipfile.ZipFile(root/'stock-framework-res.apk') as z: stock=ARSCParser(z.read('resources.arsc'))
with zipfile.ZipFile(root/'android-7-framework-res-built.apk') as z: target=ARSCParser(z.read('resources.arsc'))
refs={}
with zipfile.ZipFile(root/'AfpHome-port-unsigned.apk') as z:
 for name in z.namelist():
  if name!='resources.arsc' and not name.endswith('.xml'):continue
  data=z.read(name)
  for offset in range(0,len(data)-3,4):
   value=struct.unpack_from('<I',data,offset)[0]
   if value>>24!=1:continue
   resource=stock.get_resource_xml_name(value,'android')
   if not resource:continue
   key=(value,resource)
   refs.setdefault(key,[]).append({'file':name,'offset':offset})
report=[]
for (value,name),locations in sorted(refs.items()):
 at_target=target.get_resource_xml_name(value,'android')
 kind,key=name.lstrip('@').split('/',1)
 replacement=target.get_res_id_by_key('android',kind,key)
 report.append({'stock_id':f'0x{value:08x}','stock_name':name,'target_name_at_same_id':at_target,
  'target_id_for_name':f'0x{replacement:08x}' if replacement else None,'same_id_and_name':name==at_target,'locations':locations})
out={'target':'actual built Android7 framework-res','references':report,
 'warning':'Aligned word scan includes false positives; offsets must be parsed as typed resources/XML attributes before any rewriting. DEX, reflection and runtime are not covered.'}
(root/'afphome-binary-resource-audit.json').write_text(json.dumps(out,indent=2))
print('Framework resource candidates:',len(report),'mismatched IDs:',sum(not x['same_id_and_name'] for x in report))
for x in report:
 if not x['same_id_and_name']: print(x['stock_id'],x['stock_name'],'=>',x['target_name_at_same_id'],'name replacement',x['target_id_for_name'])
