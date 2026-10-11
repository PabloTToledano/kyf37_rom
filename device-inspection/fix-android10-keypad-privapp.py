from pathlib import Path
root=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
(root/'permissions/privapp-permissions-kyf37-keypad.xml').write_text('<permissions><privapp-permissions package="org.kyf37.keypad"><permission name="android.permission.WRITE_SECURE_SETTINGS"/></privapp-permissions></permissions>\n')
p=root/'device.mk';s=p.read_text()
line='PRODUCT_COPY_FILES += device/kyocera/kyf37/permissions/privapp-permissions-kyf37-keypad.xml:system/etc/permissions/privapp-permissions-kyf37-keypad.xml'
if line not in s: p.write_text(s.rstrip()+'\n'+line+'\n')
print('ok')
