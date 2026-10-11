"""Reconstruct remaining owner Kyocera APK candidates without enabling them in ROM.

Preserves existing ports and original package/provider contracts. Never declares
assembly equivalent to runtime compatibility, and never replaces Android 10 libs.
"""
from pathlib import Path
import argparse,subprocess,zipfile,re,json,shutil,runpy
here=Path(__file__).resolve().parent;ws=here.parent;r=Path('/home/pablo/kyf37-rom');tree=Path('/home/pablo/kyf37-android10')
parser=argparse.ArgumentParser();parser.add_argument('--modules',nargs='*');args=parser.parse_args()
inventory=json.loads((ws/'kyf37-rom/all-stock-app-ports/inventory.json').read_text())
felicaClients={'MobileFeliCaClient','MobileFeliCaSettingApp','MobileFeliCaWebPlugin','MobileFeliCaWebPluginBoot','Edy4FP'}
selected=[x for x in inventory if (x['kyocera_package'] or x['module'] in felicaClients) and (x['status'] in ['not-ported','inventory/review-required'] or x['status'].startswith('candidate-')) and (not args.modules or x['module'] in args.modules)]
stage=r/'remaining-stock-ports';stage.mkdir(exist_ok=True)
dest=tree/'packages/apps/Kyf37RemainingStockApps';dest.mkdir(exist_ok=True)
java=Path('/home/pablo/kyf37-host-tools/jdk8/bin/java')
def run(*a):subprocess.run([str(x) for x in a],check=True,stdout=subprocess.DEVNULL)
resource=runpy.run_path(str(here/'stock-resource-compat.py'))
ids=resource['framework_map'](r/'stock-system/framework/framework-res.apk',tree/'out/target/product/kyf37/system/framework/framework-res.apk',tree/'out/host/linux-x86/bin/aapt2')
oldResources=resource['resource_names'](r/'stock-system/framework/framework-res.apk',tree/'out/host/linux-x86/bin/aapt2')
newResources=set(resource['resource_names'](tree/'out/target/product/kyf37/system/framework/framework-res.apk',tree/'out/host/linux-x86/bin/aapt2').values())
resourceAudit=runpy.run_path(str(here/'audit-stock-resource-refs.py'))
boot=set()
for module in ['framework','telephony-common','voip-common','ims-common','core-oj','core-libart','ext']:
 jar=tree/f'out/target/common/obj/JAVA_LIBRARIES/{module}_intermediates/classes.jar'
 if jar.exists():
  with zipfile.ZipFile(jar) as z:boot.update(n[:-6] for n in z.namelist() if n.endswith('.class'))
compat=set()
for coreModule in ['core-oj','core-libart','org.apache.http.legacy']:
 coreJar=tree/f'out/soong/.intermediates/libcore/{coreModule}/android_common/javac/{coreModule}.jar'
 if coreModule=='org.apache.http.legacy':coreJar=tree/f'out/target/common/obj/JAVA_LIBRARIES/{coreModule}_intermediates/classes.jar'
 if coreJar.exists():
  with zipfile.ZipFile(coreJar) as z:boot.update(n[:-6] for n in z.namelist() if n.endswith('.class'))
for p in (r/'kyocera-compat-stage').rglob('*.smali'):
 m=re.search(r'^\.class[^\n]*? L([^;]+);',p.read_text(),re.M)
 if m:compat.add(m[1])
legacy={}
for folder in [r/'stock-dialer-port/legacy-framework-smali',r/'vendor-framework-smali',r/'kc-framework-smali',r/'base-framework-smali',r/'remaining-stock-shared-libraries']:
 for p in folder.rglob('*.smali'):
  m=re.search(r'^\.class[^\n]*? L([^;]+);',p.read_text(),re.M)
  if m and m[1] not in boot and m[1] not in compat:legacy.setdefault(m[1],p)
with zipfile.ZipFile(ws/'kyf37-rom/SystemUI-stock.apk') as z:
 artwork={p.split('/')[-1]:z.read(p) for p in z.namelist() if p.startswith('res/drawable-hdpi-v4/') and p.split('/')[-1] in ['k_i_co_btn_softkey_base.png','k_c_co_btn_softkey_left_up_normal.png','k_c_co_btn_softkey_left_down_normal.png','k_c_co_btn_softkey_center_normal.png','k_c_co_btn_softkey_right_up_normal.png','k_c_co_btn_softkey_right_down_normal.png']}
reports=[]
adapters=runpy.run_path(str(here/'prepare-stock-app-adapters.py'))
adapterSmali=adapters['prepare']()
for item in selected:
 name=item['module'];work=stage/name;work.mkdir(exist_ok=True);smali=work/'smali'
 if smali.exists():shutil.rmtree(smali) # Owned reconstruction stage only; never stock/source backups.
 smali.mkdir();apk=Path(item['stock_apk']);added=[];refs=set();defined=set()
 with zipfile.ZipFile(apk) as z:
  dexFiles=[n for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
  if dexFiles:
   for n in dexFiles:
    (work/n).write_bytes(z.read(n));run(java,'-jar',r/'tools/baksmali.jar','disassemble',work/n,'-o',smali)
  elif item['deodexed_dex']:run(java,'-jar',r/'tools/baksmali.jar','disassemble',item['deodexed_dex'][0],'-o',smali)
 pruned=adapters['prune'](smali,apk)
 adaptations=adapters['adapt'](smali,adapterSmali)
 modernPermissions=set()
 if 'setWifiApEnabled' in adaptations:modernPermissions.add('android.permission.NETWORK_STACK')
 if 'setBacklightBrightness' in adaptations:modernPermissions.add('android.permission.CONTROL_DISPLAY_BRIGHTNESS')
 if 'endCall' in adaptations:modernPermissions.add('android.permission.ANSWER_PHONE_CALLS')
 if 'getPackageSizeInfo' in adaptations:modernPermissions.add('android.permission.PACKAGE_USAGE_STATS')
 if 'isIdle' in adaptations or 'isOffhook' in adaptations:modernPermissions.add('android.permission.READ_PHONE_STATE')
 if 'getKeyguardStoredPasswordQuality' in adaptations or 'isSecure' in adaptations:modernPermissions.add('android.permission.ACCESS_KEYGUARD_SECURE_STORAGE')
 resourceClasses=runpy.run_path(str(here/'rebuild-stock-appcompat-resources.py'))['rebuild'](smali,apk,tree)
 for p in smali.rglob('*.smali'):
  m=re.search(r'^\.class[^\n]*? L([^;]+);',p.read_text(),re.M)
  if m:defined.add(m[1])
 known=boot|compat|defined;queue=list(smali.rglob('*.smali'))
 while queue:
  p=queue.pop();text=p.read_text()
  for cls in re.findall(r'L([A-Za-z_$][\w$]*(?:/[A-Za-z_$][\w$]*)+);',text):
   if '/' not in cls or '.' in cls:continue
   refs.add(cls)
   if cls in known or cls not in legacy:continue
   target=smali/(cls+'.smali');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(legacy[cls],target)
   added.append(cls);known.add(cls);queue.append(target)
 resourceRefs=resourceAudit['literals'](smali)
 trackedIds=resourceAudit['TrackedMap'](ids)
 for p in smali.rglob('*.smali'):
  text=p.read_text()
  # Deoptimized intrinsic references can name private specialized overloads.
  # Public Object-arraycopy preserves their behavior and is callable on Android 10.
  text=re.sub(r'Ljava/lang/System;->arraycopy\(\[[BCDFIJSZ]I\[[BCDFIJSZ]II\)V','Ljava/lang/System;->arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V',text)
  text=re.sub(r'(?<![\w])0x1[0-9a-fA-F]{6}(?![\w])',lambda m:hex(ids.get(int(m[0],16),int(m[0],16))),text)
  text=re.sub(r'invoke-virtual(?P<range>/range)? (?P<regs>\{[^}]*\}), Landroid/view/Window;->(?P<name>getSoftkeyGuide|getCurrentSoftkeys|getAttributSoftkeys|setSoftkeys)(?P<desc>\([^\n\s]+)',lambda m:'invoke-static'+(m['range'] or '')+' '+m['regs']+', Ljp/kyocera/kcfp/util/Kyf37SoftkeyBridge;->'+m['name']+'(Landroid/view/Window;'+m['desc'][1:],text)
  p.write_text(text)
 hasDex=bool(list(smali.rglob('*.smali')))
 if hasDex:run(java,'-jar',r/'tools/smali.jar','assemble',smali,'-o',work/'classes.dex')
 module='Kyf37Stock'+re.sub(r'\W','_',name);out=dest/(module+'.apk');native=[];missingNative=[]
 with zipfile.ZipFile(apk) as zin,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as zout:
  have=set()
  for entry in zin.infolist():
   if entry.filename.startswith('META-INF/') or entry.filename.endswith('.dex'):continue
   data=zin.read(entry.filename)
   if entry.filename=='AndroidManifest.xml' and modernPermissions:
    data=runpy.run_path(str(here/'stock-manifest-compat.py'))['add_permissions'](data,sorted(modernPermissions))
   if entry.filename=='resources.arsc' or entry.filename=='AndroidManifest.xml' or (entry.filename.startswith('res/') and entry.filename.endswith('.xml')):data=resource['remap_binary'](data,trackedIds)
   zout.writestr(entry,data);have.add(entry.filename)
  if hasDex:zout.write(work/'classes.dex','classes.dex');zout.write(r/'kyocera-compat.dex','classes2.dex')
  for lib in (apk.parent/'lib/arm').glob('*.so'):
   source=lib
   if not source.is_file():source=r/'stock-system/lib'/lib.name
   if not source.is_file():missingNative.append(lib.name);continue
   entry='lib/armeabi-v7a/'+lib.name
   if entry not in have:zout.write(source,entry)
   native.append(lib.name)
  for asset,data in artwork.items():zout.writestr('assets/kyf37-native-softkeys/'+asset,data)
  zout.writestr('assets/kyf37-native-softkeys/package.txt',item['package'])
 report={'stock_module':name,'build_module':module,'package':item['package'],'status':'candidate-assembled/not-enabled/not-hardware-verified','bundled_legacy_classes':added,'missing_classes':sorted(refs-known),'native_libraries':native,'missing_native_libraries':missingNative,'shared_uid':item['shared_uid'],'has_dex':hasDex,'uses_library_manifest':item['uses_library_manifest'],'resource_class_reconstruction':resourceClasses}
 report.update({'unused_appcompat':pruned,'service_adaptations':adaptations})
 report['modern_adapter_permissions']=sorted(modernPermissions)
 report['missing_framework_resources']=[{'id':hex(i),'name':oldResources[i]} for i in sorted(resourceRefs|trackedIds.references) if i in oldResources and oldResources[i] not in newResources]
 (work/'report.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
 print(name,'assembled; missing classes='+str(len(report['missing_classes'])),'native libs='+str(len(native)),flush=True)
allReports=[json.loads(p.read_text()) for p in sorted(stage.glob('*/report.json'))]
mk=['LOCAL_PATH := $(call my-dir)\n']
for item in allReports:
 module=item['build_module']
 required='LOCAL_REQUIRED_MODULES := Kyf37NextFpUtil Kyf37NextFpUtilPermissions\n' if item['stock_module'] in ['EmgBuzzApp','Edy4FP'] else ''
 mk.append(f'''include $(CLEAR_VARS)
LOCAL_MODULE := {module}
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := {module}.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := platform
LOCAL_DEX_PREOPT := false
LOCAL_USE_AAPT2 := false
{required}
include $(BUILD_PREBUILT)
''')
mk.append(runpy.run_path(str(here/'stage-remaining-stock-shared-library.py'))['stage'](dest))
(dest/'Android.mk').write_text('\n'.join(mk))
(ws/'kyf37-rom/all-stock-app-ports/assembly-reports.json').write_text(json.dumps(allReports,indent=2)+'\n')
print('Candidate modules available:',len(allReports),'; PRODUCT_PACKAGES unchanged')
