#!/usr/bin/env python3
"""Stage the backlight HAL where the vendor HIDL loader can find it."""
from pathlib import Path
import shutil

host = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
tree = Path('/home/pablo/kyf37-android10')
source = host / 'kyf37-rom/android10-lights'
dest = tree / 'device/kyocera/kyf37/lights'
def write(path, content):
    if not path.exists() or path.read_text() != content:
        path.write_text(content)
shutil.copytree(source, dest, dirs_exist_ok=True)
p = dest / 'Android.mk'
s = p.read_text()
if 'LOCAL_VENDOR_MODULE := true' not in s:
    s = s.replace('LOCAL_MODULE := lights.kyf37',
                  'LOCAL_MODULE := lights.kyf37\nLOCAL_VENDOR_MODULE := true')
write(p, s)
p = tree / 'device/kyocera/kyf37/device.mk'
s = p.read_text()
for entry in ('PRODUCT_PACKAGES += lights.kyf37',
              'PRODUCT_PROPERTY_OVERRIDES += ro.hardware.lights=kyf37'):
    if entry not in s:
        s += '\n' + entry + '\n'
write(p, s)
p = tree / 'device/kyocera/kyf37/Android.mk'
s = p.read_text()
entry = 'include $(LOCAL_PATH)/lights/Android.mk'
if entry not in s:
    s += '\n# Standard backlight HAL (subdirectories are not auto-included).\n' + entry + '\n'
write(p, s)
print('Brightness HAL staged in vendor/lib/hw for Android 10 light HIDL')
