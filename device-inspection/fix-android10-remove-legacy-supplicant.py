"""Remove Lollipop-era wpa_supplicant/p2p_supplicant services from the ramdisk init.qcom.rc (they shadow the Android 10 HIDL service). WSL."""
import re
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/ramdisk/init.qcom.rc')
s = p.read_text()
for name in ('p2p_supplicant', 'wpa_supplicant'):
    s, n = re.subn(r'^service %s /system/bin/wpa_supplicant.*?\n\n' % name, '', s, flags=re.M | re.S)
    print(name, 'removed' if n else 'already absent')
p.write_text(s)
