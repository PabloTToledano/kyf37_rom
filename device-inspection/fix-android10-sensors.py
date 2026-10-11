"""Stage the supplemental sensor HAL without replacing the stock accelerometer."""
from pathlib import Path
import shutil, re

ws = Path(__file__).resolve().parent.parent
tree = Path('/home/pablo/kyf37-android10')
dest = tree/'device/kyocera/kyf37/sensors'
dest.mkdir(exist_ok=True)
def put(path, text):
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
for src in (ws/'device-inspection/sensors').glob('*'):
    if src.is_file():
        target = dest/src.name
        if not target.exists() or target.read_bytes() != src.read_bytes():
            shutil.copyfile(src, target)
put(dest/'hals.conf', '/system/lib/hw/sensors.default.so\n/vendor/lib/hw/sensors.kyf37_extra.so\n')
p = tree/'device/kyocera/kyf37/device.mk'
s = p.read_text()
for line in ('PRODUCT_PACKAGES += sensors.kyf37_extra',
             'PRODUCT_COPY_FILES += device/kyocera/kyf37/sensors/hals.conf:$(TARGET_COPY_OUT_VENDOR)/etc/sensors/hals.conf'):
    if line not in s:
        s += '\n' + line + '\n'
put(p, s)
p = tree/'hardware/interfaces/sensors/1.0/default/android.hardware.sensors@1.0-service.rc'
put(p, re.sub(r'(?m)^([ \t]*group system wakelock uhid)(?: input)*[ \t]*$',
              r'\1 input', p.read_text()))
print('OEM accelerometer + supplemental light/motion/step/lid HAL staged')
