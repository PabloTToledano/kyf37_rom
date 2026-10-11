from pathlib import Path
import json,re,subprocess
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom');stock=Path('/home/pablo/kyf37-rom/stock-system')
r=json.loads((host/'stock-native-dependencies.json').read_text());log=Path('/home/pablo/kyf37-lineage-build.log').read_text(errors='replace')
paths=sorted(set(re.findall(r"overriding commands for target `[^']*/system/([^']+)'",log)))
core={'bin/rild','bin/wcnss_service','lib/egl/libGLES_android.so','lib/libETC1.so','lib/libspeexresampler.so','lib/libtinyalsa.so','lib/libtinycompress.so'}
rows=[]
for x in paths:
 rows.append({'path':x,'preferred_provider':'target Android platform' if x in core else 'requires model HAL/provider review','stock_dependencies':r['elf'].get(x,{}).get('needed',[])})
for x in sorted(set(r['proprietary_dependency_candidates']) & core):
 if x not in paths:rows.append({'path':x,'preferred_provider':'target Android platform','stock_dependencies':r['elf'].get(x,{}).get('needed',[])})
(host/'native-provider-conflicts.json').write_text(json.dumps({'conflicts':rows,'note':'Do not finalize copying until symbol/ABI validation; Android core daemons and runtime libraries must not be downgraded to stock5.1. Model HAL selection is deliberate, not resolved by copy-order warnings.'},indent=2))
print('Conflicting installed paths:',len(rows))
print('Platform replacements:',[x['path'] for x in rows if x['preferred_provider']=='target Android platform'])
