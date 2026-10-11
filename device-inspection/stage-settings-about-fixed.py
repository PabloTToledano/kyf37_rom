from pathlib import Path
import zipfile,shutil
r=Path('/home/pablo/kyf37-android10/out/target/product/kyf37')
p=r/'system/product/priv-app/Settings/Settings.apk'
with zipfile.ZipFile(p) as z:
 dex=[i for i in z.namelist() if i.endswith('.dex')];print('DEX',dex)
 if not dex:raise SystemExit('No DEX: must package unstripped signed APK for data update')
shutil.copy2(p,'/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/Settings-about-fixed.apk')
