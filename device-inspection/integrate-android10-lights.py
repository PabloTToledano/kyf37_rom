from pathlib import Path
import shutil
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
tree=Path('/home/pablo/kyf37-android10')
shutil.copytree(host/'kyf37-rom/android10-lights',tree/'device/kyocera/kyf37/lights',dirs_exist_ok=True)
p=tree/'device/kyocera/kyf37/device.mk'
entry='PRODUCT_PACKAGES += lights.kyf37'
s=p.read_text()
if entry not in s:s+='\n'+entry+'\nPRODUCT_PROPERTY_OVERRIDES += ro.hardware.lights=kyf37\n'
p.write_text(s)
print('Added standard lights HAL for evidenced LCD/keypad sysfs nodes')
