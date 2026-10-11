"""Recover stock shared Java libraries into a dependency reference stage only."""
from pathlib import Path
import zipfile,subprocess
r=Path('/home/pablo/kyf37-rom');stage=r/'remaining-stock-shared-libraries';stage.mkdir(exist_ok=True);java='/home/pablo/kyf37-host-tools/jdk8/bin/java'
for name in ['com.nextfp.android.util','jp.kyocera.morpho.rapideffect.api.EffectManager','core-junit','hiddenlib','libdfkcfpdummy']:
 jar=r/'stock-system/framework'/(name+'.jar');work=stage/name;work.mkdir(exist_ok=True)
 with zipfile.ZipFile(jar) as z:
  dex=[n for n in z.namelist() if n.endswith('.dex')]
  for n in dex:(work/Path(n).name).write_bytes(z.read(n))
 if not dex:
  bootDex=r/'stock-system/framework/arm/boot.oat-dex'/(name+'.dex')
  odex=r/'stock-system/framework/arm'/(name+'.odex')
  if bootDex.exists():(work/(name+'.dex')).write_bytes(bootDex.read_bytes())
  else:subprocess.run([java,'-jar',str(r/'tools/oat2dex.jar'),'-o',str(work),str(odex),str(r/'stock-system/framework/arm/boot.oat-dex')],check=True)
 for p in work.rglob('*.dex'):
  subprocess.run([java,'-jar',str(r/'tools/baksmali.jar'),'disassemble',str(p),'-o',str(work/'smali')],check=True)
 print(name,'classes',len(list((work/'smali').rglob('*.smali'))),flush=True)
