import json,re
from pathlib import Path
from androguard.core.dex import DEX
from loguru import logger
logger.remove()
root=Path('kyf37-rom')
dex=DEX((root/'AfpHome-softkey-port.dex').read_bytes())
uris=sorted({s for s in dex.get_strings() if s.startswith('content://') and len(s)>len('content://')})
inventory=json.loads((root/'stock-app-inventory.json').read_text())
report=[]
for uri in uris:
 authority=uri[len('content://'):].split('/',1)[0]
 providers=[]
 for app in inventory:
  tree=app.get('manifest_tree','')
  declarations=re.findall(r'android:authorities[^\n]*?="([^"]+)"',tree)
  if any(authority in declaration.split(';') for declaration in declarations):providers.append(app['path'])
 report.append({'uri':uri,'authority':authority,'stock_provider_apks':providers})
(root/'afphome-provider-dependencies.json').write_text(json.dumps({'literal_uri_dependencies':report,'note':'Literal DEX strings only; absence from inventory is not proof a provider does not exist. No providers have been ported or tested by this audit.'},indent=2))
print('Literal content URI dependencies:',len(report))
for item in report:print(item['uri'],'stock provider:',', '.join(item['stock_provider_apks']) or 'not resolved in inventory')
