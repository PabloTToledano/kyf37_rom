"""Offline stock FeliCa inventory; no chip, phone or provisioning operations."""
from pathlib import Path
import subprocess,re,json
tree=Path('/home/pablo/kyf37-android10');stock=Path('/home/pablo/kyf37-rom/stock-system');product=tree/'out/target/product/kyf37/system'
aapt=tree/'out/host/linux-x86/bin/aapt2';items=[]
for directory in sorted((stock/'app').iterdir()):
 if not any(word in directory.name.lower() for word in ['felica','edy4']):continue
 for apk in directory.glob('*.apk'):
  text=subprocess.check_output([str(aapt),'dump','badging',str(apk)],text=True)
  package=re.search(r"package: name='([^']+)'",text)[1]
  label=re.search(r"application-label:'([^']*)'",text)
  launch=re.search(r"launchable-activity: name='([^']+)'",text)
  items.append({'stock_module':directory.name,'package':package,'label':label[1] if label else None,'launcher_activity':launch[1] if launch else None,'built_module_apks':[str(p.relative_to(product)) for p in product.rglob(apk.name)]})
configs={}
for p in [tree/'device/kyocera/kyf37/kernel.config',Path('/home/pablo/kyf37-rom/kernel-android10/.config')]:
 if p.exists():configs[str(p)]=[line for line in p.read_text().splitlines() if 'CONFIG_KFELICA' in line or line.startswith('CONFIG_NFC')]
report={'stock_felica_apps':items,'kernel_config_evidence':configs,'android10_nfc_apks':[str(p.relative_to(product)) for p in product.rglob('Nfc*.apk')],'hardware_verified':False}
out=Path(__file__).resolve().parent.parent/'kyf37-rom/felica-audit.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
