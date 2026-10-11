from pathlib import Path
p=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/device.mk')
s=p.read_text()
pk=Path('/home/pablo/kyf37-android10/packages/apps/Kyf37StockApps/packages.txt').read_text().strip()
s=s.replace('PRODUCT_PACKAGES += Camera2 Kyf37KeypadSettings','PRODUCT_PACKAGES += Kyf37KeypadSettings')
line='PRODUCT_PACKAGES += '+pk
if 'jp.kyocera.android.hardware.KCCameraEx' not in s:
    s=s.rstrip()+'\n'+line+'\n'
p.write_text(s)
print(line)
