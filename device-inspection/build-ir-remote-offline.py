"""Build independent APK from a locked-build ARM helper; no phone access.
Run build-locked.sh <log> kyf37_ir_tx first. Uses local SDK and platform signing.
"""
from pathlib import Path
import os,subprocess,shutil,zipfile,hashlib
ws=Path(__file__).resolve().parent.parent
root=Path.home()/'kyf37-android10';src=ws/'device-inspection/ir-remote'
out=Path.home()/'kyf37-rom/ir-remote-offline';out.mkdir(exist_ok=True)
deliver=ws/'kyf37-rom/ir-remote';deliver.mkdir(exist_ok=True)
env=os.environ.copy();jdk=root/'prebuilts/jdk/jdk8/linux-x86';env['JAVA_HOME']=str(jdk);env['PATH']=str(jdk/'bin')+':'+env['PATH']
env['LD_LIBRARY_PATH']=str(root/'out/host/linux-x86/lib64')+':'+env.get('LD_LIBRARY_PATH','')
def run(*args):
    print('RUN',str(args[0]),flush=True)
    subprocess.run(list(map(str,args)),env=env,check=True)
helper=out/'kyf37_ir_tx'
built=root/'out/target/product/kyf37/system/bin/kyf37_ir_tx'
assert built.exists(),'Build kyf37_ir_tx with build-locked.sh first'
native=root/'packages/apps/Kyf37Remote/native'
for name in ('kyf37_ir_tx.c','kyf37_ir_uapi.h'):
    assert (native/name).read_bytes()==(src/name).read_bytes(),'Re-stage helper source before building'
assert built.stat().st_mtime >= max((native/n).stat().st_mtime for n in ('kyf37_ir_tx.c','kyf37_ir_uapi.h')),'Rebuild helper after source update'
shutil.copy2(built,helper)
classes=out/'classes';classes.mkdir(exist_ok=True)
sdk=root/'prebuilts/sdk/28/public/android.jar'
run(jdk/'bin/javac','-source','8','-target','8','-classpath',sdk,'-d',classes,src/'IrSignals.java',src/'Remote.java')
jar=out/'classes.jar'
run(jdk/'bin/jar','cf',jar,'-C',classes,'.')
dex=out/'dex';dex.mkdir(exist_ok=True)
run(jdk/'bin/java','-cp',root/'prebuilts/r8/r8-master.jar','com.android.tools.r8.D8','--min-api','23','--lib',sdk,'--output',dex,jar)
assets=out/'assets';assets.mkdir(exist_ok=True);shutil.copy2(helper,assets/'kyf37_ir_tx')
manifest=root/'packages/apps/Kyf37Remote/AndroidManifest.xml'
unsigned=out/'Kyf37Remote-unsigned.apk'
run(root/'out/host/linux-x86/bin/aapt2','link','--manifest',manifest,'-I',sdk,'-A',assets,'-o',unsigned)
with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_DEFLATED) as z:z.write(dex/'classes.dex','classes.dex')
aligned=out/'Kyf37Remote-aligned.apk'
run(root/'out/host/linux-x86/bin/zipalign','-f','4',unsigned,aligned)
apk=deliver/'Kyf37Remote.apk'
signer=root/'prebuilts/sdk/tools/linux/lib/apksigner.jar'
run(jdk/'bin/java','-jar',signer,'sign','--key',root/'build/make/target/product/security/platform.pk8','--cert',root/'build/make/target/product/security/platform.x509.pem','--out',apk,aligned)
run(jdk/'bin/java','-jar',signer,'verify','--verbose',apk)
shutil.copy2(helper,deliver/helper.name)
for name in ('Remote.java','IrSignals.java','IrSignalsTest.java','kyf37_ir_tx.c','kyf37_ir_uapi.h','kyf37_ir_kernel.inc'):shutil.copy2(src/name,deliver/name)
(deliver/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(deliver.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print('Built offline:',apk,'No phone access. Custom GPIO kernel still requires validated matching ROM deployment.')
