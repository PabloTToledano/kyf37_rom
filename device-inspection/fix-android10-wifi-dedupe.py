import re
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/device.mk')
s = p.read_text()
s = re.sub(r'\\n\s*device/kyocera/kyf37/\w*supplicant\w*\.conf:system/vendor/etc/wifi/\w+\.conf', '', s)
s = re.sub(r'\s*device/kyocera/kyf37/\w*supplicant\w*\.conf:system/vendor/etc/wifi/\w+\.conf', '', s)
p.write_text(s)
print([l[:150] for l in s.splitlines() if 'wifi.rc' in l or 'vendor/etc/wifi' in l])
