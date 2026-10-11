"""Write evidence-based readiness matrix; static checks never mean ready on phone."""
from pathlib import Path
import json
ws=Path(__file__).resolve().parent.parent;folder=ws/'kyf37-rom/all-stock-app-ports'
apps=json.loads((folder/'assembly-reports.json').read_text());apis={x['module']:x for x in json.loads((folder/'api-audits.json').read_text())}
native=json.loads((folder/'native-audits.json').read_text())['files'];shared={x['module']:x for x in json.loads((folder/'shared-library-audits.json').read_text())}
signed={x['module']:x for x in json.loads((folder/'signed-artifacts.json').read_text())} if (folder/'signed-artifacts.json').exists() else {}
rows=[]
for app in apps:
 name=app['stock_module'];api=apis.get(name,{})
 issues=[]
 if app['missing_classes']:issues.append('unresolved classes: '+', '.join(app['missing_classes']))
 if app.get('missing_framework_resources'):issues.append('missing original framework resources')
 if app['missing_native_libraries']:issues.append('missing native payloads')
 if api.get('missing_methods') or api.get('missing_fields'):issues.append('legacy framework API contracts unresolved')
 if any(x['missing_libraries'] or x['unresolved_strong_symbols'] for x in native if x['module']==name):issues.append('JNI dependency symbols unresolved')
 if any(x['missing_required'] for x in shared.get(name,{}).get('libraries',[])):issues.append('required shared library absent')
 if name.startswith('FeliCa') or name.startswith('MobileFeliCa') or name in ['felicaservice','Edy4FP']:issues.append('FeliCa service, device access, trust/provisioning and secure-element behavior unverified')
 if name in ['AfpHome','lifesettings','Readout']:issues.append('original audio streams/routing need adaptation')
 if name=='InfoServer':issues.append('legacy DefaultContainerService absent; data-collection backend migration required')
 if name=='IrDATransfer':issues.append('custom vCard provider contract unresolved; UART ownership must coexist with FeliCa')
 if name=='sysupdater':issues.append('original stock OTA updater must be replaced with owner-ROM update flow before activation')
 if name in ['SupportMDM','Start_SetupWizard','InfoChild','InfoServer','news','weathernews','aumall','mbok']:issues.append('legacy service/provider/carrier endpoint behavior unverified')
 issues.append('offline candidate; not installed or hardware verified')
 row={'module':name,'package':app['package'],'signed_artifact':signed.get(name),'missing_classes':len(app['missing_classes']),'missing_apis':len(api.get('missing_methods',[]))+len(api.get('missing_fields',[])),'missing_resources':len(app.get('missing_framework_resources',[])),'blockers':issues,'ready':False}
 rows.append(row)
(folder/'readiness.json').write_text(json.dumps(rows,indent=2)+'\n')
(folder/'readiness.md').write_text('# Stock app port readiness\n\nEvery row is an offline candidate. Zero static failures does not establish runtime compatibility. Existing six selected ports, flashlight replacement, stock dialer and One Seg TV have separate status documents.\n\n| Module | Classes | APIs | Resources | Signed | Remaining checks/blockers |\n|---|---:|---:|---:|---|---|\n'+''.join('| '+x['module']+' | '+str(x['missing_classes'])+' | '+str(x['missing_apis'])+' | '+str(x['missing_resources'])+' | '+('yes' if x['signed_artifact'] else 'no')+' | '+'; '.join(x['blockers'])+' |\n' for x in rows))
print('Candidates',len(rows),'API-clear',sum(x['missing_apis']==0 for x in rows),'resource-clear',sum(x['missing_resources']==0 for x in rows),'hardware-ready',sum(x['ready'] for x in rows))
