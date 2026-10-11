"""Compile narrow service adapters and prune provably unreferenced AppCompat code.

No unresolved resource IDs are invented. A string or XML reference prevents pruning.
"""
from pathlib import Path
import subprocess,re,zipfile,shutil
here=Path(__file__).resolve().parent;r=Path('/home/pablo/kyf37-rom')
def prepare():
 stage=r/'remaining-stock-adapters';stage.mkdir(exist_ok=True)
 classes=stage/'classes';classes.mkdir(exist_ok=True)
 java=Path('/home/pablo/kyf37-host-tools/jdk8/bin')
 def run(*args):subprocess.run([str(a) for a in args],check=True,stdout=subprocess.DEVNULL)
 run(java/'javac','-source','7','-target','7','-bootclasspath',here.parent/'kyf37-rom/android-7-sdk-classes.jar','-d',classes,here/'kyocera-port/Kyf37StockAppCompat.java',here/'kyocera-port/Kyf37MonthlyCycle.java',here/'kyocera-port/Kyf37MediaQuery.java',here/'kyocera-port/Kyf37CharacterInput.java')
 run(java/'java','-jar','/home/pablo/kyf37-lineage/prebuilts/sdk/tools/lib/dx.jar','--dex','--output='+str(stage/'adapter.dex'),classes)
 run(java/'java','-jar',r/'tools/baksmali.jar','disassemble',stage/'adapter.dex','-o',stage/'smali')
 return stage/'smali'
def prune(smali,apk):
 prefix='android/support/v7/';folder=smali/prefix
 if not folder.exists():return {'pruned':False}
 references=[]
 for p in smali.rglob('*.smali'):
  if str(p.relative_to(smali)).startswith(prefix):continue
  if re.search(r'android[/\.]support[/\.]v7',p.read_text()):references.append(str(p.relative_to(smali)))
 with zipfile.ZipFile(apk) as z:
  for name in z.namelist():
   if name=='AndroidManifest.xml' or name=='resources.arsc' or name.startswith(('res/','assets/')):
    data=z.read(name)
    if any(token in data for token in [b'android.support.v7',b'android/support/v7','android.support.v7'.encode('utf-16-le')]):references.append(name)
 if references:return {'pruned':False,'external_references':references}
 count=len(list(folder.rglob('*.smali')))
 shutil.rmtree(folder)
 return {'pruned':True,'classes':count,'reason':'no external bytecode, reflection-string, manifest, resource or asset references'}
def adapt(smali,adapters):
 counts={};helper='Lorg/kyf37/stockcompat/Kyf37StockAppCompat;'
 for p in list(smali.rglob('*.smali')):
  text=p.read_text()
  original=text
  if str(p).endswith('/jp/kyocera/charactercheck/CharacterCheckActivity.smali'):
   body='''.method private bR()V
    .registers 3
    iget v0, p0, Ljp/kyocera/charactercheck/CharacterCheckActivity;->mState:I
    iput v0, p0, Ljp/kyocera/charactercheck/CharacterCheckActivity;->gn:I
    const/4 v0, 0x1
    iput v0, p0, Ljp/kyocera/charactercheck/CharacterCheckActivity;->mState:I
    iget-object v0, p0, Ljp/kyocera/charactercheck/CharacterCheckActivity;->gm:Ljava/lang/String;
    invoke-static {p0, v0}, Lorg/kyf37/stockcompat/Kyf37CharacterInput;->show(Landroid/app/Activity;Ljava/lang/String;)V
    return-void
.end method'''
   text,n=re.subn(r'\.method private bR\(\)V.*?\.end method',lambda m:body,text,flags=re.S)
   assert n==1
   counts['characterInputDialog']=n
  if str(p).endswith('/jp/kyocera/datafolder/bean/Folder.smali'):
   def sense_query(m):
    body=m[0]
    old='invoke-virtual/range {v0 .. v5}, Landroid/content/ContentResolver;->query(Landroid/net/Uri;[Ljava/lang/String;Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Landroid/database/Cursor;'
    assert old in body
    counts['mediaSenseQuery']=counts.get('mediaSenseQuery',0)+1
    return body.replace(old,'invoke-static/range {v0 .. v5}, Lorg/kyf37/stockcompat/Kyf37MediaQuery;->sense(Landroid/content/ContentResolver;Landroid/net/Uri;[Ljava/lang/String;Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Landroid/database/Cursor;')
   text=re.sub(r'\.method public computeMediatSense\([^\n]*.*?\.end method',sense_query,text,flags=re.S)
  pattern=r'invoke-(static|virtual)(/range)? (\{[^}]*\}), L(android/os/Environment|android/telephony/PhoneNumberUtils|android/os/PowerManager);->(getSecondaryStorageDirectory|getSecondaryStorageState|getUsbStorageDirectory|getUsbStorageState|formatNumberEx|setBacklightBrightness)(\([^\s]+)'
  def change(m):
   kind,rng,regs,owner,name,desc=m.groups()
   expected={'getSecondaryStorageDirectory':'()Ljava/io/File;','getSecondaryStorageState':'()Ljava/lang/String;','getUsbStorageDirectory':'()Ljava/io/File;','getUsbStorageState':'()Ljava/lang/String;','formatNumberEx':'(Ljava/lang/String;)Ljava/lang/String;','setBacklightBrightness':'(I)V'}[name]
   if desc!=expected:raise RuntimeError('Unexpected adapter descriptor '+m[0])
   if kind=='virtual':desc='(L'+owner+';'+desc[1:]
   counts[name]=counts.get(name,0)+1
   return 'invoke-static'+(rng or '')+' '+regs+', '+helper+'->'+name+desc
  changed=re.sub(pattern,change,text)
  legacy=r'invoke-(?:virtual|interface)(/range)? (\{[^}]*\}), L(com/android/internal/telephony/ITelephony|com/android/internal/widget/LockPatternUtils);->(endCall|isIdle|isOffhook|getKeyguardStoredPasswordQuality|isLockScreenDisabled|isSecure|isBiometricWeakInstalled|usingBiometricWeak)(\(\)[ZI])'
  def migrate(m):
   rng,regs,owner,name,desc=m.groups();counts[name]=counts.get(name,0)+1
   return 'invoke-static'+(rng or '')+' '+regs+', '+helper+'->'+name+'(Ljava/lang/Object;)'+desc[-1]
  changed=re.sub(legacy,migrate,changed)
  ap=r'invoke-virtual(/range)? (\{[^}]*\}), Landroid/net/wifi/WifiManager;->setWifiApEnabled\(Landroid/net/wifi/WifiConfiguration;Z\)Z'
  def hotspot(m):
   counts['setWifiApEnabled']=counts.get('setWifiApEnabled',0)+1
   return 'invoke-static'+(m[1] or '')+' '+m[2]+', '+helper+'->setWifiApEnabled(Ljava/lang/Object;Landroid/net/wifi/WifiConfiguration;Z)Z'
  changed=re.sub(ap,hotspot,changed)
  for method in ('computeLastCycleBoundary','computeNextCycleBoundary'):
   old='Landroid/net/NetworkPolicyManager;->'+method+'(JLandroid/net/NetworkPolicy;)J'
   if old in changed:
    counts[method]=counts.get(method,0)+changed.count(old)
    changed=changed.replace(old,helper+'->'+method+'(JLjava/lang/Object;)J')
  cycle_field=r'iget (v\d+|p\d+), (v\d+|p\d+), Landroid/net/NetworkPolicy;->cycleDay:I'
  def cycle_day(m):
   counts['getCycleDay']=counts.get('getCycleDay',0)+1
   return 'invoke-static {'+m[2]+'}, '+helper+'->getCycleDay(Ljava/lang/Object;)I\n\n    move-result '+m[1]
  changed=re.sub(cycle_field,cycle_day,changed)
  package_size=r'invoke-virtual(/range)? (\{[^}]*\}), Landroid/content/pm/PackageManager;->getPackageSizeInfo\(Ljava/lang/String;ILandroid/content/pm/IPackageStatsObserver;\)V'
  def package_stats(m):
   counts['getPackageSizeInfo']=counts.get('getPackageSizeInfo',0)+1
   return 'invoke-static'+(m[1] or '')+' '+m[2]+', '+helper+'->getPackageSizeInfo(Ljava/lang/Object;Ljava/lang/String;ILjava/lang/Object;)V'
  changed=re.sub(package_size,package_stats,changed)
  old_profile='Landroid/provider/ContactsContract$Profile;->getContactLookupUri(Landroid/content/ContentResolver;)Landroid/net/Uri;'
  if old_profile in changed:
   counts['getContactLookupUri']=counts.get('getContactLookupUri',0)+changed.count(old_profile)
   changed=changed.replace(old_profile,helper+'->getContactLookupUri(Landroid/content/ContentResolver;)Landroid/net/Uri;')
  old='Landroid/provider/Settings$System;->getBuzzerSoundsUri(Landroid/content/Context;I)Landroid/net/Uri;'
  if old in changed:
   counts['getBuzzerSoundsUri']=counts.get('getBuzzerSoundsUri',0)+changed.count(old)
   changed=changed.replace(old,helper+'->getBuzzerSoundsUri(Landroid/content/Context;I)Landroid/net/Uri;')
  if changed!=original:p.write_text(changed)
 if counts:
  for p in adapters.rglob('*.smali'):
   target=smali/p.relative_to(adapters);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 return counts
