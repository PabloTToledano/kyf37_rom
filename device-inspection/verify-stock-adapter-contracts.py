"""Verify newly used reflection targets against actual compiled Android classes."""
from pathlib import Path
import zipfile,subprocess,json,re
here=Path(__file__).resolve().parent;tree=Path('/home/pablo/kyf37-android10')
out=Path('/home/pablo/kyf37-rom/stock-adapter-contracts');out.mkdir(exist_ok=True)
jars=[tree/f'out/target/common/obj/JAVA_LIBRARIES/{name}_intermediates/classes.jar' for name in ['framework','core-oj','core-libart']]
jars+=[tree/f'out/soong/.intermediates/libcore/{name}/android_common/javac/{name}.jar' for name in ['core-oj','core-libart']]
contracts={
 'android/net/NetworkPolicy':['public android.util.RecurrenceRule cycleRule;'],
 'android/util/RecurrenceRule':['public final java.time.ZonedDateTime start;','public boolean isMonthly();'],
 'java/time/ZonedDateTime':['public int getDayOfMonth();','public java.time.ZoneId getZone();'],
 'android/app/ApplicationPackageManager':['public android.content.pm.ApplicationInfo getApplicationInfoAsUser(java.lang.String, int, int)'],
 'android/content/pm/ApplicationInfo':['public java.util.UUID storageUuid;'],
 'android/os/UserHandle':['public static android.os.UserHandle of(int);'],
 'android/app/usage/StorageStatsManager':['public android.app.usage.StorageStats queryStatsForPackage(java.util.UUID, java.lang.String, android.os.UserHandle)'],
 'android/app/usage/StorageStats':['public long getAppBytes();','public long getDataBytes();','public long getCacheBytes();'],
 'android/content/pm/PackageStats':['public android.content.pm.PackageStats(java.lang.String, int);','public long codeSize;','public long dataSize;','public long cacheSize;'],
 'android/provider/ContactsContract$Profile':['public static final android.net.Uri CONTENT_URI;','public static final android.net.Uri CONTENT_RAW_CONTACTS_URI;'],
 'android/provider/ContactsContract$Contacts':['public static android.net.Uri getLookupUri(android.content.ContentResolver, android.net.Uri);'],
}
results=[]
for owner,signatures in contracts.items():
 source=None;blob=None
 for jar in jars:
  if not jar.exists():continue
  with zipfile.ZipFile(jar) as z:
   if owner+'.class' in z.namelist():source=jar;blob=z.read(owner+'.class');break
 if blob is None:raise RuntimeError('Compiled Android class absent: '+owner)
 local=out/(owner.replace('/','_')+'.class');local.write_bytes(blob)
 text=subprocess.check_output(['/home/pablo/kyf37-host-tools/jdk8/bin/javap','-p',str(local)],text=True)
 for signature in signatures:
  if signature not in text:raise RuntimeError('Reflection contract absent: '+owner+' '+signature)
 results.append({'class':owner,'compiled_source':str(source),'contracts':signatures})
report={'passed':True,'classes':results,'phone_accessed':False,'scope':'Compiled member signatures only; permissions/appops, provider execution and reflection runtime remain unverified'}
(here.parent/'kyf37-rom/all-stock-app-ports/adapter-contracts.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified reflection contracts in',len(results),'compiled Android classes')
