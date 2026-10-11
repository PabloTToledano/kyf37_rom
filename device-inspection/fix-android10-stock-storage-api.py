"""Migrate shipped stock apps' removable-storage calls to Android 10 volumes.

Preserve the existing app resources, camera fixes and native softkey helper DEX.
Runs after native-softkey staging; no framework replacement is required.
"""
from pathlib import Path
import runpy, subprocess, shutil, zipfile, re
here=Path(__file__).resolve().parent
tree=Path('/home/pablo/kyf37-android10')
work=Path('/home/pablo/kyf37-rom/stock-storage-api');work.mkdir(exist_ok=True)
java='/home/pablo/kyf37-host-tools/jdk8/bin/java'
tools=Path('/home/pablo/kyf37-rom/tools')
def run(*args): subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)
adapters=None
for apk in (tree/'packages/apps/Kyf37StockApps').glob('*.apk'):
    stage=work/apk.stem;stage.mkdir(exist_ok=True)
    with zipfile.ZipFile(apk) as z: raw=z.read('classes.dex')
    (stage/'input.dex').write_bytes(raw)
    smali=stage/'smali'
    if smali.exists(): shutil.rmtree(smali) # Only our disposable disassembly.
    run(java,'-jar',tools/'baksmali.jar','disassemble',stage/'input.dex','-o',smali)
    count=0
    for p in smali.rglob('*.smali'):
        s=p.read_text()
        for old,new in [('getRemovableStorageDirectory','getSecondaryStorageDirectory'),
                        ('getRemovableStorageState','getSecondaryStorageState')]:
            needle='Landroid/os/Environment;->'+old
            count+=s.count(needle)
            s=s.replace(needle,'Lorg/kyf37/stockcompat/Kyf37StockAppCompat;->'+new)
        p.write_text(s)
    if not count: continue
    if adapters is None:
        adapters=runpy.run_path(str(here/'prepare-stock-app-adapters.py'))['prepare']()
    shutil.copytree(adapters,smali,dirs_exist_ok=True)
    run(java,'-jar',tools/'smali.jar','assemble',smali,'-o',stage/'classes.dex')
    tmp=apk.with_suffix('.storage.tmp')
    with zipfile.ZipFile(apk) as zin,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            if info.filename.startswith('META-INF/') or info.filename=='classes.dex': continue
            zout.writestr(info,zin.read(info.filename))
        zout.write(stage/'classes.dex','classes.dex')
    tmp.replace(apk)
    print(apk.stem, count, 'legacy removable-storage calls migrated',flush=True)
