"""Verify candidate APKs with Android's APK verifier on API 29, platform cert.

Builds only an isolated host verifier from the existing Android tools/apksig source.
Never reads signing private keys or touches phone/system-image staging.
"""
from pathlib import Path
import subprocess,shutil,json,hashlib,re,sys,zipfile
here=Path(__file__).resolve().parent;folder=here.parent/'kyf37-rom/all-stock-app-ports';tree=Path('/home/pablo/kyf37-android10');java=Path('/home/pablo/kyf37-host-tools/jdk8/bin');stage=Path('/home/pablo/kyf37-rom/remaining-apk-verifier');classes=stage/'classes';classes.mkdir(parents=True,exist_ok=True)
source=tree/'tools/apksig/src';files=list((source/'main/java').rglob('*.java'))+list((source/'apksigner/java').rglob('*.java'))
if not files:raise RuntimeError('Existing Android APK verifier source missing')
fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(files))).hexdigest()
stamp=stage/'source.sha256'
if not stamp.exists() or stamp.read_text()!=fingerprint:
 result=subprocess.run([str(java/'javac'),'-source','8','-target','8','-d',str(classes),*[str(p) for p in files]],capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stderr)
 stamp.write_text(fingerprint)
dest=classes/'com/android/apksigner';dest.mkdir(exist_ok=True)
for resource in (source/'apksigner/java/com/android/apksigner').glob('*.txt'):shutil.copy2(resource,dest/resource.name)
if '--prepare-only' in sys.argv:print('Isolated Android APK signature verifier compiled');sys.exit(0)
cert=subprocess.check_output(['openssl','x509','-in',str(tree/'build/make/target/product/security/platform.x509.pem'),'-outform','DER'])
expected=hashlib.sha256(cert).hexdigest();reports=[]
assembly={x['stock_module']:x for x in json.loads((folder/'assembly-reports.json').read_text())}
for item in json.loads((folder/'signed-artifacts.json').read_text()):
 apk=folder/'signed-apks'/item['file']
 result=subprocess.run([str(java/'java'),'-cp',str(classes),'com.android.apksigner.ApkSignerTool','verify','--verbose','--print-certs','--min-sdk-version','29',str(apk)],capture_output=True,text=True)
 digest=re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)',result.stdout)
 report={'module':item['module'],'api_level':29,'verified':result.returncode==0 and digest==[expected],'platform_cert_sha256':expected,'stdout':result.stdout,'stderr':result.stderr}
 sourceApk=tree/'packages/apps/Kyf37RemainingStockApps'/item['file']
 with zipfile.ZipFile(sourceApk) as sourceZip,zipfile.ZipFile(apk) as signedZip:
  payloads=[n for n in sourceZip.namelist() if n in ['AndroidManifest.xml','resources.arsc','classes.dex','classes2.dex'] or n.startswith(('assets/kyf37-native-softkeys/','lib/armeabi-v7a/'))]
  if any(sourceZip.read(n)!=signedZip.read(n) for n in payloads):raise RuntimeError(item['module']+' signed payload differs from current reconstructed source')
  report['source_payload_matches']=True
 permissions=subprocess.check_output([str(tree/'out/host/linux-x86/bin/aapt2'),'dump','permissions',str(apk)],text=True)
 required=assembly[item['module']].get('modern_adapter_permissions',[])
 if any("name='"+permission+"'" not in permissions for permission in required):raise RuntimeError(item['module']+' adapter permission absent from signed manifest')
 report['modern_adapter_permissions_verified']=required
 reports.append(report)
 if not report['verified']:raise RuntimeError(item['module']+' verification failed: '+result.stdout+result.stderr)
(folder/'signature-verification.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Android APK signature verification passed:',len(reports),'candidates, API 29, expected platform public certificate')
