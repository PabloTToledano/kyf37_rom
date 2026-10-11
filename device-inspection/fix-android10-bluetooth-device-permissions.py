from pathlib import Path
p=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/ramdisk/ueventd.qcom.rc')
s=p.read_text()
for dev in ('smd2','smd3'):
 import re
 s,n=re.subn(r'(^/dev/'+dev+r'\s+0660\s+bluetooth\s+)3008\s*$',r'\1bluetooth',s,flags=re.M)
 assert n==1 or re.search(r'^/dev/'+dev+r'\s+0660\s+bluetooth\s+bluetooth$',s,re.M)
p.write_text(s)
print('Bluetooth SMD nodes use valid bluetooth owner/group; mode 0660 retained')
