from pathlib import Path
r=Path('/home/pablo/kyf37-android10');p=r/'device/kyocera/kyf37/ramdisk/init.target.rc';print('\n'.join(p.read_text().splitlines()[130:160]));print('\n'.join((r/'device/kyocera/kyf37/ramdisk/init.qcom.rc').read_text().splitlines()[390:412]))
p=r/'out/target/product/kyf37/root/init.target.rc';print('built exists',p.exists());print('wcnss in productrc', 'wcnss-service' in p.read_text() if p.exists() else False)
