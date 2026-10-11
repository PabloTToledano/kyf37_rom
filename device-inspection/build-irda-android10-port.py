from pathlib import Path
import subprocess,shutil,zipfile,os
root=Path('/home/pablo/kyf37-android10');r=Path('/home/pablo/kyf37-rom');stage=r/'irda-compat'
jdk=Path('/home/pablo/kyf37-host-tools/jdk8/bin')
(stage/'classes').mkdir(exist_ok=True)
def run(args,**kw):subprocess.run([str(x) for x in args],check=True,**kw)
run([jdk/'javac','-source','7','-target','7','-bootclasspath','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/android-7-sdk-classes.jar','-d',stage/'classes',*list((stage/'src').rglob('*.java'))])
run([jdk/'java','-jar','/home/pablo/kyf37-lineage/prebuilts/sdk/tools/lib/dx.jar','--dex','--output='+str(stage/'adapter.dex'),stage/'classes'])
run([jdk/'java','-jar',r/'tools/baksmali.jar','disassemble',stage/'adapter.dex','-o',stage/'adapter-smali'])
app=stage/'app-smali';shutil.copytree(r/'irda-port-smali',app,dirs_exist_ok=True)
shutil.copytree(r/'kyocera-compat/helper-smali',app,dirs_exist_ok=True)
shutil.copytree(stage/'adapter-smali',app,dirs_exist_ok=True)
for p in (r/'vendor-framework-smali/jp/kyocera/felicaservice').glob('IFeliCaServiceUartExclusion*.smali'):
 dst=app/'jp/kyocera/felicaservice'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
for p in (r/'vendor-framework-smali/com/kyocera/mdm').glob('*.smali'):
 if p.name.startswith(('IMdmPolicyManager','IConfigChangedListener','OnConfigChangedListener')):
  dst=app/'com/kyocera/mdm'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
run([jdk/'java','-jar',r/'tools/smali.jar','assemble',app,'-o',stage/'classes.dex'])
with zipfile.ZipFile(r/'stock-system/priv-app/IrDATransfer/IrDATransfer.apk') as old,zipfile.ZipFile(stage/'IrDATransfer-unsigned.apk','w',zipfile.ZIP_DEFLATED) as out:
 for info in old.infolist():
  if info.filename.startswith('META-INF/') or info.filename.endswith('.dex'):continue
  out.writestr(info,old.read(info.filename))
 out.write(stage/'classes.dex','classes.dex');out.write(r/'stock-system/lib/libDc3pIrSimple.so','lib/armeabi-v7a/libDc3pIrSimple.so')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(root/'out/host/linux-x86/lib64')
run([jdk/'java','-Djava.library.path='+str(root/'out/host/linux-x86/lib64'),'-jar',root/'out/host/linux-x86/framework/signapk.jar',root/'build/make/target/product/security/platform.x509.pem',root/'build/make/target/product/security/platform.pk8',stage/'IrDATransfer-unsigned.apk',stage/'IrDATransfer.apk'],env=env)
shutil.copy2(stage/'IrDATransfer.apk','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/IrDATransfer-android10-port.apk')
print('Infrared APK port assembled and platform-signed; UART backend is real, device transfer untested')

