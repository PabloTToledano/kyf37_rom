"""Prepare and validate identity/registration changes without editing an active tree."""
from pathlib import Path
import subprocess,difflib,json,argparse,fcntl
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
here=Path(__file__).resolve().parent;tree=Path('/home/pablo/kyf37-android10')
out=here.parent/'kyf37-rom/felica-foundation';out.mkdir(exist_ok=True)
changes={};original={}
rel='system/core/libcutils/include/private/android_filesystem_config.h'
s=(tree/rel).read_text();original[rel]=s;anchor='#define AID_NFC 1027'
assert anchor in s
if '#define AID_KMFC' in s:assert '#define AID_KMFC 9000' in s
changes[rel]=s if '#define AID_KMFC' in s else s.replace(anchor,'#define AID_KMFC 9000            /* KYF37 stock FeliCa identity */\n'+anchor,1)
(out/'android_filesystem_config.h').write_text(changes[rel])
array=subprocess.check_output(['/home/pablo/kyf37-host-tools/python2/bin/python',str(tree/'build/make/tools/fs_config/fs_config_generator.py'),'aidarray',str(out/'android_filesystem_config.h')],text=True)
assert '"kmfc", AID_KMFC' in array or '"kmfc", 9000' in array, 'Generated Android identity absent'
(out/'android_ids.h').write_text(array)
rel='frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java'
s=(tree/rel).read_text();original[rel]=s;anchor='''        mSettings.addSharedUserLPw("android.uid.nfc", NFC_UID,
                ApplicationInfo.FLAG_SYSTEM, ApplicationInfo.PRIVATE_FLAG_PRIVILEGED);'''
assert anchor in s
changes[rel]=s if 'mSettings.addSharedUserLPw("android.uid.felica", 9000,' in s else s.replace(anchor,anchor+'''\n        // Original KYF37 FeliCa clients use the OEM kmfc identity, not a new app UID.
        mSettings.addSharedUserLPw("android.uid.felica", 9000,
                ApplicationInfo.FLAG_SYSTEM, ApplicationInfo.PRIVATE_FLAG_PRIVILEGED);''',1)
rel='device/kyocera/kyf37/sepolicy/seapp_contexts'
s=(tree/rel).read_text();original[rel]=s
rule='user=kmfc seinfo=platform domain=platform_app type=app_data_file'
changes[rel]=s if rule in s.splitlines() else s.rstrip()+'\n'+rule+'\n'
rel='frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=(tree/rel).read_text();original[rel]=s;anchor='android.os.ServiceManager.addService("jp.kyocera.felicaservice.FeliCaServiceUartExclusion", new Kyf37UartBroker(mContext));'
assert anchor in s
changes[rel]=s if '"ro.kyf37.felica.oem_service"' in s else s.replace(anchor,'if (!android.os.SystemProperties.getBoolean("ro.kyf37.felica.oem_service", false)) { '+anchor+' }',1)
patch=''.join(''.join(difflib.unified_diff((tree/rel).read_text().splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)) for rel,new in changes.items())
(out/'identity-and-broker.patch').write_text(patch)
if args.apply:
 with Path('/home/pablo/kyf37-build.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert all((tree/rel).read_text()==s for rel,s in original.items()), 'Sources changed; regenerate before applying'
  for rel,new in changes.items():
   if original[rel]!=new:(tree/rel).write_text(new)
(out/'identity-validation.json').write_text(json.dumps({'stock_uid':9000,'native_identity_generator_passed':True,'patch_prepared':True,'tree_modified':args.apply,'compiled_framework':False,'service_enabled':False,'phone_accessed':False,'required_before_activation':['Compile matching framework/SELinux/native identity changes','Enable original UART service only with OEM stack selection','Resolve original certificate and JNI/service contracts','Hardware chip communication without changing payment provisioning']},indent=2)+'\n')
print('kmfc UID 9000 accepted by Android identity generator; identity patch applied:',args.apply,'chip initialized: false')
