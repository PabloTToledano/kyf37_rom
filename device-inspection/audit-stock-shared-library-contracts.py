"""Audit required/optional manifest library contracts against product permissions."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
ws=Path(__file__).resolve().parent.parent;tree=Path('/home/pablo/kyf37-android10');folder=ws/'kyf37-rom/all-stock-app-ports'
libraries={}
for base in [tree/'out/target/product/kyf37/system/etc/permissions',tree/'out/target/product/kyf37/system/product/etc/permissions']:
 for p in base.glob('*.xml'):
  try:root=ET.parse(p).getroot()
  except ET.ParseError:continue
  for item in root.findall('library'):libraries[item.get('name')]={'definition':str(p),'file':item.get('file'),'state':'product-definition'}
libraries['com.nextfp.android.util']={'file':'/system/framework/com.nextfp.android.util.jar','state':'optional-candidate-library/activation-required'}
rows=[]
for app in json.loads((folder/'assembly-reports.json').read_text()):
 deps=[]
 for manifest in app['uses_library_manifest']:
  name=re.search(r'android:name[^\n]*?="([^"]+)"',manifest)
  if not name:raise RuntimeError('Cannot parse library '+manifest)
  required=not re.search(r'android:required[^\n]*?=false',manifest)
  deps.append({'name':name[1],'required':required,'provider':libraries.get(name[1]),'missing_required':required and name[1] not in libraries})
 rows.append({'module':app['stock_module'],'libraries':deps})
(folder/'shared-library-audits.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:
 if row['libraries']:print(row['module'],[(d['name'],d['required'],d['provider'] is not None) for d in row['libraries']])
