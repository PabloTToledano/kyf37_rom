"""KYF37 owner item 6: USB debugging always on and accepts any computer. Idempotent; WSL Python 3.

 * boot ramdisk (package-android10-legacy-boot.py default.prop): ro.adb.secure 1 -> 0 (adbd needs no key auth,
   no on-screen dialog). Takes effect only with a newly packaged boot image (v19).
 * device.mk fallback props ro.adb.secure=0 (ignored if ramdisk already set it - ro.* is write-once) and persist.sys.usb.config=adb.
"""
from pathlib import Path
import re
WS = Path(__file__).resolve().parent.parent
ROOT = Path('/home/pablo/kyf37-android10')

p = WS / 'device-inspection/package-android10-legacy-boot.py'
s = p.read_text(encoding='utf-8')
if "replace('ro.adb.secure=1','ro.adb.secure=0')" not in s:
    s = s.replace("        props=props.replace('persist.sys.usb.config=none','persist.sys.usb.config=adb')\n",
      "        props=props.replace('persist.sys.usb.config=none','persist.sys.usb.config=adb')\n"
      "        props=props.replace('ro.adb.secure=1','ro.adb.secure=0')  # owner: any computer, no auth dialog\n", 1)
    p.write_bytes(s.encode('utf-8')); print('patched', p.name)

# adb_enabled itself: AdbService.systemReady() sets Global adb_enabled=1 whenever persist.sys.usb.config contains
# 'adb', so the persist prop below is what makes it default-on (also after a data reset).
mk = ROOT / 'device/kyocera/kyf37/device.mk'
m = mk.read_text()
if 'Kyf37 adb default' not in m:
    m += '\n# Kyf37 adb default (owner: USB debugging always on, any computer)\nPRODUCT_PROPERTY_OVERRIDES += ro.adb.secure=0 persist.sys.usb.config=adb\n'
    mk.write_text(m); print('device.mk props')
