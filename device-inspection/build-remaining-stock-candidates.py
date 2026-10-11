"""Build signed package intermediates only; do not install optional apps into image."""
from pathlib import Path
import subprocess,json,hashlib,shutil,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--collect-existing',action='store_true',help='Collect existing signed intermediates only; run signature/source verifier afterward. Does not certify a successful build.')
args=parser.parse_args()
here=Path(__file__).resolve().parent;ws=here.parent;tree=Path('/home/pablo/kyf37-android10');folder=ws/'kyf37-rom/all-stock-app-ports'
reports=json.loads((folder/'assembly-reports.json').read_text())
targets=['out/target/product/kyf37/obj/APPS/'+x['build_module']+'_intermediates/package.apk' for x in reports]
log=Path('/home/pablo/remaining-stock-candidates-build.log')
if not args.collect_existing:
 subprocess.run(['bash',str(here/'build-locked.sh'),str(log),*targets,'services'],check=True)
 if 'BUILD_EXIT=0' not in log.read_text().splitlines()[-1]:raise RuntimeError('Build failed; inspect '+str(log))
dest=folder/'signed-apks';dest.mkdir(exist_ok=True);out=[]
for item,target in zip(reports,targets):
 source=tree/target;apk=dest/(item['build_module']+'.apk');shutil.copy2(source,apk)
 out.append({'module':item['stock_module'],'file':apk.name,'bytes':apk.stat().st_size,'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'hardware_verified':False})
(folder/'signed-artifacts.json').write_text(json.dumps(out,indent=2)+'\n')
shutil.copy2(log,folder/'build.log')
shared=folder/'shared-libraries';shared.mkdir(exist_ok=True)
for name in ['com.nextfp.android.util.jar','com.nextfp.android.util.xml']:
 shutil.copy2(tree/'packages/apps/Kyf37RemainingStockApps'/name,shared/name)
print('Signed',len(out),'optional candidates; total bytes',sum(x['bytes'] for x in out),flush=True)
(folder/'artifact-collection.json').write_text(json.dumps({'collected_existing':args.collect_existing,'build_exit_verified':not args.collect_existing,'requires_signature_and_source_verification':True,'build_log':str(log)},indent=2)+'\n')
