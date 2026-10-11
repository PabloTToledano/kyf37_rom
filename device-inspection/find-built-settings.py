from pathlib import Path
r=Path('/home/pablo/kyf37-android10/out/target/product/kyf37')
for p in r.rglob('Settings.apk'):print(p)
