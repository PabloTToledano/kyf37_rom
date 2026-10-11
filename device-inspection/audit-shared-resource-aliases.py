from pathlib import Path
import json,zipfile
from loguru import logger
from androguard.core.axml import ARSCParser
logger.remove()
root=Path('kyf37-rom')
maps=json.loads((root/'afphome-shared-resource-map.json').read_text())['aliases']
with zipfile.ZipFile(root/'stock-framework-res.apk') as z:
 stock=ARSCParser(z.read('resources.arsc'))
with zipfile.ZipFile(root/'android-7-sdk-classes.jar') as z:
 target=ARSCParser(z.read('resources.arsc'))
rows=[]
for alias,name in maps['mResName'].items():
 kind=maps['mResType'][alias]
 rid=stock.get_res_id_by_key('android',kind,name)
 assert rid is not None,(kind,name)
 modern=target.get_res_id_by_key('android',kind,name)
 configs=[{'qualifiers':config.get_qualifier(),'value':value}
          for config,value in stock.get_resolved_res_configs(rid)]
 rows.append({'alias':alias,'type':kind,'name':name,'stock_id':f'0x{rid:08x}',
              'sdk25_has_named_resource':modern is not None,'stock_configs':configs})
(root/'afphome-shared-resource-alias-audit.json').write_text(json.dumps({
 'resources':rows,'note':'SDK25 baseline, not final compiled ROM resources; names present do not prove matching content/state behavior.'},indent=2),encoding='utf8')
print('Checked',len(rows),'aliases; absent from SDK25:',sum(not x['sdk25_has_named_resource'] for x in rows))
