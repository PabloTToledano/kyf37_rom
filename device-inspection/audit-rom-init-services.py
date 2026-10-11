from pathlib import Path
import re,json
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom');stock=Path('/home/pablo/kyf37-rom/stock-system')
services=[]
for p in (host/'stock-boot-ramdisk').glob('*.rc'):
 for line in p.read_text().splitlines():
  m=re.match(r'^service\s+(\S+)\s+(\S+)',line)
  if not m:continue
  name,path=m.groups();file=stock/path[len('/system/'):] if path.startswith('/system/') else None
  services.append({'source':p.name,'name':name,'executable':path,'stock_file_exists':file.exists() if file else None})
report=json.loads((host/'stock-native-dependencies.json').read_text())
candidates=set(report['proprietary_dependency_candidates'])
missing=[x for x in services if x['stock_file_exists'] and x['executable'][len('/system/'):] not in candidates]
(host/'stock-init-service-audit.json').write_text(json.dumps({'services':services,'stock_service_executables_not_staged':missing},indent=2))
print('Services',len(services),'stock executables not staged',len(missing))
for x in missing:print(x['name'],x['executable'])
