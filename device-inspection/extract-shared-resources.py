from pathlib import Path
import zipfile,json,re
from lxml import etree
from loguru import logger
from androguard.core.axml import ARSCParser,AXMLPrinter
logger.remove()
root=Path('kyf37-rom');out=root/'shared-resource-assets/res';out.mkdir(parents=True,exist_ok=True)
aliases=json.loads((root/'afphome-shared-resource-map.json').read_text())['aliases']
trees={};manifest=[]
with zipfile.ZipFile(root/'stock-framework-res.apk') as z:
 arsc=ARSCParser(z.read('resources.arsc'))
 pending=[arsc.get_res_id_by_key('android',aliases['mResType'][alias],name)
          for alias,name in aliases['mResName'].items()]
 assert all(pending)
 done=set()
 while pending:
  rid=pending.pop()
  if rid in done:continue
  done.add(rid)
  kind,name=arsc.get_resource_xml_name(rid,'android').lstrip('@').split('/',1)
  for config,value in arsc.get_resolved_res_configs(rid):
   qualifier=config.get_qualifier()
   if isinstance(value,str) and value.startswith('res/'):
    data=z.read(value)
    if value.endswith('.xml'):
     xml=AXMLPrinter(data).get_xml().decode()
     def symbolic(match):
      ref=int(match.group(1),16);pending.append(ref)
      mapped=arsc.get_resource_xml_name(ref,'android')
      assert mapped,hex(ref)
      return mapped
     data=re.sub(r'@(?:android:)?([0-9a-fA-F]{8})',symbolic,xml).encode()
    dest=out/value.removeprefix('res/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    manifest.append({'id':hex(rid),'name':name,'type':kind,'qualifiers':qualifier,'source':value})
   else:
    assert kind in ('string','color','dimen','integer','bool'),(kind,name,value)
    folder='values'+('-'+qualifier if qualifier else '')
    tree=trees.setdefault(folder,etree.Element('resources'))
    item=etree.SubElement(tree,kind,name=name)
    if kind=='string':
     assert isinstance(value,str)
     value='"'+value.replace('\\','\\\\').replace('"','\\"').replace("'","\\'").replace('\n','\\n').replace('\r','\\r')+'"'
    item.text=str(value)
    manifest.append({'id':hex(rid),'name':name,'type':kind,'qualifiers':qualifier,'source':'values'})
 for folder,tree in trees.items():
  dest=out/folder/'kyf37_shared.xml';dest.parent.mkdir(exist_ok=True)
  dest.write_bytes(etree.tostring(tree,pretty_print=True,encoding='utf-8',xml_declaration=True))
(out.parent/'manifest.json').write_text(json.dumps({'resources':manifest,'resource_count':len(done),
 'note':'Original locale/configuration resource closure. Compiled nine-patches need source decoding; build/runtime validation pending.'},indent=2))
print('Extracted',len(done),'resource definitions in',len(manifest),'configurations')
