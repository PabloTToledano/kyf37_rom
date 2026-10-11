from pathlib import Path
tree=Path('/home/pablo/kyf37-android10')
device=tree/'device/kyocera/kyf37'
p=device/'BoardConfig.mk'
s=p.read_text().replace('BOARD_SEPOLICY_VERS := 30\n','')
p.write_text(s)
p=device/'lineage.mk'
p.write_text(p.read_text().replace('vendor/lineage/config/common_full_phone.mk','vendor/lineage/config/common_mini_phone.mk'))
print('Selected mini Go product and platform-default SELinux compatibility version')
