"""App-local MemoContract and recorder menu layout compatibility, no boot classes replaced."""
from pathlib import Path
import zipfile,shutil,subprocess
r=Path('/home/pablo/kyf37-rom'); tree=Path('/home/pablo/kyf37-android10')
stage=r/'selected-stock-runtime';stage.mkdir(exist_ok=True)
java='/home/pablo/kyf37-host-tools/jdk8/bin/java'
def run(*args):subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)
for name in ['MemoPad','MemoPadProvider','kc_soundrecorder']:
 apk=tree/'packages/apps/Kyf37StockApps'/(name+'.apk'); work=stage/name;work.mkdir(exist_ok=True)
 with zipfile.ZipFile(apk) as z:(work/'input.dex').write_bytes(z.read('classes.dex'))
 smali=work/'smali'
 if smali.exists():shutil.rmtree(smali) # Owned temporary disassembly only.
 run(java,'-jar',r/'tools/baksmali.jar','disassemble',work/'input.dex','-o',smali)
 changed=False
 if name.startswith('Memo'):
  for p in (r/'base-framework-smali/android/provider').glob('MemoContract*.smali'):
   target=smali/'android/provider'/p.name
   if not target.exists():
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);changed=True
 else:
  # Plain-text menu rows: the OEM private layout number now identifies an
  # unrelated Android 10 view. Public simple_list_item_1 has the same TextView contract.
  for p in smali.rglob('*.smali'):
   old=p.read_text(); new=old.replace('0x1090089','0x1090003')
   if new!=old:p.write_text(new);changed=True
 if not changed:continue
 run(java,'-jar',r/'tools/smali.jar','assemble',smali,'-o',work/'classes.dex')
 temp=apk.with_suffix('.runtime.tmp')
 with zipfile.ZipFile(apk) as zin,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as zout:
  for info in zin.infolist():
   if info.filename.startswith('META-INF/') or info.filename=='classes.dex':continue
   zout.writestr(info,zin.read(info.filename))
  zout.write(work/'classes.dex','classes.dex')
 temp.replace(apk);print(name,'runtime compatibility staged',flush=True)
