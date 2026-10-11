"""Recover original OEM resources and their missing dependency closure (Windows).

Run tools/stock-resource-venv/Scripts/python.exe; androguard 4.1.3, Pillow, lxml.
Modern framework names remain modern; only missing OEM names are copied.
"""
from pathlib import Path
import zipfile,json,re,subprocess,sys,itertools,functools,operator
from lxml import etree
from loguru import logger
from androguard.core.axml import ARSCParser,AXMLPrinter
logger.remove()
ws=Path(__file__).resolve().parent.parent;folder=ws/'kyf37-rom/all-stock-app-ports'
target=folder/'resource-source/res';target.mkdir(parents=True,exist_ok=True)
modern=subprocess.check_output(['wsl','-d','Ubuntu','--','/home/pablo/kyf37-android10/out/host/linux-x86/bin/aapt2','dump','resources','/home/pablo/kyf37-android10/out/target/product/kyf37/system/framework/framework-res.apk'],text=True,encoding='utf-8')
modernNames=set(re.findall(r'resource 0x[0-9a-f]+ (\S+)',modern))
apps=json.loads((folder/'assembly-reports.json').read_text())
pending=[int(item['id'],16) for app in apps for item in app.get('missing_framework_resources',[])]
attrs={}
attrRoot=etree.parse('//wsl.localhost/Ubuntu/home/pablo/kyf37-android10/frameworks/base/core/res/res/values/attrs.xml')
for item in attrRoot.findall('.//attr'):
 options=[(child.tag,child.get('name'),int(child.get('value'),0)) for child in item if child.tag in ('enum','flag')]
 if options:attrs.setdefault(item.get('name'),[]).extend(option for option in options if option not in attrs.get(item.get('name'),[]))
def numericAttribute(name,content):
 if name not in attrs or not re.fullmatch(r'-?\d+|0x[0-9a-fA-F]+',content):return content
 value=int(content,0)
 options=attrs[name]
 for kind,label,number in options:
  if number==value:return label
 if options[0][0]=='enum':raise ValueError(('Unknown enum',name,content))
 candidates=[item for item in options if item[2]>0 and item[2]&value==item[2]]
 for count in range(1,min(len(candidates),8)+1):
  for selection in itertools.combinations(candidates,count):
   if functools.reduce(operator.or_,(item[2] for item in selection),0)==value:return '|'.join(item[1] for item in selection)
 raise ValueError(('Unknown flags',name,content))
trees={};done=set();manifest=[]
with zipfile.ZipFile(ws/'kyf37-rom/stock-framework-res.apk') as z:
 arsc=ARSCParser(z.read('resources.arsc'))
 def symbolic(match):
  prefix=match[1];rid=int(match[2],16);name=arsc.get_resource_xml_name(rid,'android')
  if not name:raise ValueError('Unknown original resource '+hex(rid))
  if name.lstrip('@').replace('android:','') not in modernNames:pending.append(rid)
  return prefix+name.lstrip('@')
 while pending:
  rid=pending.pop()
  if rid in done:continue
  done.add(rid)
  full=arsc.get_resource_xml_name(rid,'android')
  if not full:raise ValueError(hex(rid))
  kind,name=full.lstrip('@').replace('android:','').split('/',1)
  if kind+'/'+name in modernNames:continue
  for config,value in arsc.get_resolved_res_configs(rid):
   qualifier=config.get_qualifier()
   if isinstance(value,str) and value.startswith('res/'):
    data=z.read(value)
    if value.endswith('.xml'):
     xml=AXMLPrinter(data).get_xml().decode('utf-8')
     xml=re.sub(r'([@?])(?:android:)?([0-9a-fA-F]{8})',symbolic,xml)
     parsed=etree.fromstring(xml.encode('utf-8'))
     for element in parsed.iter():
      for attr,content in list(element.attrib.items()):
       if attr.endswith(('}layout_width','}layout_height')) and content in ('-1','-2'):
        element.set(attr,'match_parent' if content=='-1' else 'wrap_content')
       else:element.set(attr,numericAttribute(attr.split('}')[-1],content))
     xml=etree.tostring(parsed,encoding='unicode')
     data=xml.encode('utf-8')
    dest=target/value.removeprefix('res/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
   else:
    values='values'+('-'+qualifier if qualifier else '')
    root=trees.setdefault(values,etree.Element('resources'))
    if kind=='array':
     if not isinstance(value,list):raise TypeError((kind,name,value))
     item=etree.SubElement(root,'integer-array',name=name)
     for n in value:
      if isinstance(n,(tuple,list)):n=n[-1]
      etree.SubElement(item,'item').text=str(int(n))
    elif kind in ('string','dimen','color','integer','bool'):
     item=etree.SubElement(root,kind,name=name)
     if kind=='string':value='"'+value.replace('\\','\\\\').replace('"','\\"').replace("'","\\'").replace('\n','\\n').replace('\r','\\r')+'"'
     item.text=str(value)
    else:raise TypeError((kind,name,value))
   manifest.append({'id':hex(rid),'type':kind,'name':name,'qualifiers':qualifier})
for values,root in trees.items():
 dest=target/values/'kyf37_remaining_stock.xml';dest.parent.mkdir(exist_ok=True);dest.write_bytes(etree.tostring(root,encoding='utf-8',pretty_print=True,xml_declaration=True))
(folder/'resource-source/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
subprocess.run([sys.executable,str(ws/'device-inspection/decode-selector-ninepatch.py'),'--input',str(target),'--output',str(folder/'resource-decoded/res')],check=True,cwd=ws)
print('Recovered',len(done),'OEM resource definitions;',len(manifest),'configurations')
