"""Restore the complete stock softkey guide API through an app-local Window bridge."""
from pathlib import Path
import subprocess,shutil,re,zipfile,sys
r=Path('/home/pablo/kyf37-rom');tree=Path('/home/pablo/kyf37-android10');here=Path(__file__).resolve().parent
stage=r/'native-softkey-port';stage.mkdir(exist_ok=True);src=stage/'src/jp/kyocera/kcfp/util';src.mkdir(parents=True,exist_ok=True)
for name in ['Kyf37SoftkeyBridge.java']:(src/name).write_text((here/'kyocera-port'/name).read_text(encoding='utf-8-sig'))
(src/'KCfpSoftkeyGuide.java').write_text((here/'kyocera-port/KCfpSoftkeyGuide.stub.java').read_text(encoding='utf-8-sig'))
original=here.parent/'kyf37-rom/kyocera-compat/src/jp/kyocera/kcfp/util'
(src/'KCfpKeyDispatch.java').write_text((original/'KCfpKeyDispatch.java').read_text())
(src/'Kyf37DialogSoftkeys.java').write_text((original/'KCfpDialogUtil.java').read_text().replace('KCfpDialogUtil','Kyf37DialogSoftkeys'))
classes=stage/'classes';classes.mkdir(exist_ok=True)
java=Path('/home/pablo/kyf37-host-tools/jdk8/bin')
def run(*args):subprocess.run([str(x) for x in args],check=True)
run(java/'javac','-source','7','-target','7','-bootclasspath',here.parent/'kyf37-rom/android-7-sdk-classes.jar','-d',classes,*src.glob('*.java'))
for p in (classes/'jp/kyocera/kcfp/util').glob('KCfpSoftkeyGuide*.class'):p.unlink() # Compile declarations never ship.
run(java/'java','-jar','/home/pablo/kyf37-lineage/prebuilts/sdk/tools/lib/dx.jar','--dex','--output='+str(stage/'bridge.dex'),classes)
bridge=stage/'bridge-smali';run(java/'java','-jar',r/'tools/baksmali.jar','disassemble',stage/'bridge.dex','-o',bridge)
compat=r/'kyocera-compat-stage';dest=compat/'jp/kyocera/kcfp/util'
# Restore the original rich API (including resource XML, icons, priorities and Parcelable types).
for p in (r/'vendor-framework-smali/jp/kyocera/kcfp/util').glob('KCfpSoftkeyGuide*.smali'):shutil.copy2(p,dest/p.name)
bridgeOwner='Ljp/kyocera/kcfp/util/Kyf37SoftkeyBridge;'
def redirect(text):
 pattern=r'invoke-virtual(?P<range>/range)? (?P<regs>\{[^}]*\}), Landroid/view/Window;->(?P<name>getSoftkeyGuide|getCurrentSoftkeys|getAttributSoftkeys|setSoftkeys)(?P<signature>\([^\n\s]+)'
 return re.sub(pattern,lambda m:'invoke-static'+(m['range'] or '')+' '+m['regs']+', '+bridgeOwner+'->'+m['name']+'(Landroid/view/Window;'+m['signature'][1:],text)
p=dest/'KCfpSoftkeyGuide.smali';text=redirect(p.read_text())
text=re.sub(r'invoke-virtual(?P<range>/range)? (?P<regs>\{[^}]*\}), Landroid/content/Context;->getPackageName\(\)Ljava/lang/String;',lambda m:'invoke-static'+(m['range'] or '')+' '+m['regs']+', '+bridgeOwner+'->resourcesPackage(Landroid/content/Context;)Ljava/lang/String;',text)
for method,flag in [('show',1),('hide',0)]:
 body=f'.method public {method}()V\n    .registers 3\n    iget-object v0, p0, Ljp/kyocera/kcfp/util/KCfpSoftkeyGuide;->mWindow:Landroid/view/Window;\n    const/4 v1, {hex(flag)}\n    invoke-static {{v0, v1}}, {bridgeOwner}->show(Landroid/view/Window;Z)V\n    return-void\n.end method'
 text=re.sub(r'\.method public '+method+r'\(\)V.*?\.end method',lambda m:body,text,flags=re.S)
p.write_text(text)
p=dest/'KCfpDialogUtil.smali';text=p.read_text()
body=f'.method public assignButtonToSoftkey(Landroid/app/Dialog;Z)V\n    .registers 3\n    invoke-static {{p1, p2}}, {bridgeOwner}->assignDialog(Landroid/app/Dialog;Z)V\n    return-void\n.end method'
text=re.sub(r'\.method public assignButtonToSoftkey\(Landroid/app/Dialog;Z\)V.*?\.end method',lambda m:body,text,flags=re.S);p.write_text(text)
shutil.copytree(bridge,compat,dirs_exist_ok=True)
run(java/'java','-jar',r/'tools/smali.jar','assemble',compat,'-o',r/'kyocera-compat.dex')
if '--compat-only' in sys.argv:
 print('Native bridge prepared; existing app APKs preserved');sys.exit(0)
# Preserve the current APK resources and app-specific camera fixes; change only dex bridge calls/helper dex.
modules=[]
with zipfile.ZipFile(here.parent/'kyf37-rom/SystemUI-stock.apk') as stock:
 artwork={name.split('/')[-1]:stock.read(name) for name in stock.namelist() if name.startswith('res/drawable-hdpi-v4/') and name.split('/')[-1] in ['k_i_co_btn_softkey_base.png','k_c_co_btn_softkey_left_up_normal.png','k_c_co_btn_softkey_left_down_normal.png','k_c_co_btn_softkey_center_normal.png','k_c_co_btn_softkey_right_up_normal.png','k_c_co_btn_softkey_right_down_normal.png']}
assert len(artwork)==6
for apk in (tree/'packages/apps/Kyf37StockApps').glob('*.apk'):
 name=apk.stem;app=stage/name;app.mkdir(exist_ok=True)
 with zipfile.ZipFile(apk) as z:(app/'input.dex').write_bytes(z.read('classes.dex'))
 appSmali=app/'smali';run(java/'java','-jar',r/'tools/baksmali.jar','disassemble',app/'input.dex','-o',appSmali)
 for p in appSmali.rglob('*.smali'):
  old=p.read_text();new=redirect(old)
  if new!=old:p.write_text(new)
 run(java/'java','-jar',r/'tools/smali.jar','assemble',appSmali,'-o',app/'classes.dex')
 temp=apk.with_suffix('.softkey.tmp')
 with zipfile.ZipFile(apk) as zin,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as zout:
  for info in zin.infolist():
   if info.filename.startswith(('META-INF/','assets/kyf37-native-softkeys/')) or info.filename in ('classes.dex','classes2.dex'):continue
   zout.writestr(info,zin.read(info.filename))
  zout.write(app/'classes.dex','classes.dex');zout.write(r/'kyocera-compat.dex','classes2.dex')
  for assetName,data in artwork.items():zout.writestr('assets/kyf37-native-softkeys/'+assetName,data)
 temp.replace(apk);modules.append(name)
for apk in (tree/'packages/apps/Kyf37RemainingStockApps').glob('*.apk'):
 with zipfile.ZipFile(apk) as zin:
  # These already-ported apps own context-sensitive guides too. Preserve their
  # application dex/resources and package marker; replace only the helper dex.
  names=zin.namelist()
  if 'classes2.dex' not in names:continue
  old=zin.read('classes2.dex')
  if b'Kyf37SoftkeyBridge' not in old:continue
  new=(r/'kyocera-compat.dex').read_bytes()
  if old==new:continue
  temp=apk.with_suffix('.softkey.tmp')
  with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as zout:
   for info in zin.infolist():
    if info.filename.startswith('META-INF/'):continue
    zout.writestr(info,new if info.filename=='classes2.dex' else zin.read(info.filename))
 temp.replace(apk);modules.append(apk.stem)
(stage/'modules.txt').write_text(' '.join(modules))
print('Softkey bridge restored in:', ' '.join(modules))
