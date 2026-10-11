"""Add Kyocera's AE/AWB algorithm libraries that mm-camera's stats module dlopen()s (aec init failed without them). WSL; idempotent."""
import shutil
from pathlib import Path
root = Path('/home/pablo/kyf37-android10/vendor/kyocera/kyf37')
src = Path('/home/pablo/kyf37-rom/stock-system/vendor/lib')
names = ['libCipo_ae.so', 'libCipo_awb.so']
(root/'proprietary/vendor/lib').mkdir(parents=True, exist_ok=True)
lst = root/'proprietary-files.txt'; text = lst.read_text()
mk = root/'kyf37-vendor.mk'; mt = mk.read_text()
for n in names:
    shutil.copy2(src/n, root/'proprietary/vendor/lib'/n)
    line = 'vendor/lib/' + n
    if line not in text.splitlines(): text = text.rstrip('\n') + '\n' + line + '\n'
    cp = 'PRODUCT_COPY_FILES += vendor/kyocera/kyf37/proprietary/vendor/lib/%s:system/vendor/lib/%s' % (n, n)
    if cp not in mt: mt = mt.rstrip('\n') + '\n' + cp + '\n'
lst.write_text(text); mk.write_text(mt)
# KyoceraCamera replaces the other camera apps in the image
a = Path('/home/pablo/kyf37-android10/packages/apps/Kyf37StockApps/Android.mk'); s = a.read_text()
s = s.replace('LOCAL_MODULE := KyoceraCamera\n', 'LOCAL_MODULE := KyoceraCamera\nLOCAL_OVERRIDES_PACKAGES := Snap Camera2 LibreCamera\n', 1)
a.write_text(s)
print('cipo libs staged; installed names:', names)
