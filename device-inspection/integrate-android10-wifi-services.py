"""Stage the CRC-verified rebuilt WLAN driver and actual Android 10 services."""
from pathlib import Path
import subprocess, json, hashlib, xml.etree.ElementTree as ET
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0, 'Stop the build before modifying its inputs'
tree = Path('/home/pablo/kyf37-android10')
device = tree/'device/kyocera/kyf37'
host = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
audit = json.loads((host/'android10-rebuilt-wlan-audit.json').read_text())['modules']
assert len(audit)==1 and audit[0]['checked_import_crcs']>=250
assert not audit[0]['crc_mismatches'] and not audit[0]['missing_exports']
source = Path('/home/pablo/kyf37-rom/wlan-prima-caf-123/wlan.ko')
assert hashlib.sha256(source.read_bytes()).hexdigest()==audit[0]['sha256']
target = tree/'vendor/kyocera/kyf37/proprietary/lib/modules/pronto/pronto_wlan.ko'
strip = Path('/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-strip')
subprocess.run([str(strip), '-g', '-o', str(target), str(source)],check=True)
mk = device/'device.mk'
marker = '# Android 10 legacy Wi-Fi, GNSS and memory tracking services'
if marker not in mk.read_text():
    mk.write_text(mk.read_text()+'\n'+marker+'''
PRODUCT_PACKAGES += android.hardware.wifi@1.0-service wpa_supplicant hostapd \
    android.hardware.gnss@1.0-service android.hardware.gnss@1.0-impl \
    android.hardware.memtrack@1.0-service android.hardware.memtrack@1.0-impl
''')
board = device/'BoardConfig.mk'
if 'WIFI_DRIVER_MODULE_PATH :=' not in board.read_text():
    board.write_text(board.read_text()+'''
# Exact rebuilt external module; no force-loading or CRC bypass.
WIFI_DRIVER_MODULE_PATH := /system/lib/modules/pronto/pronto_wlan.ko
WIFI_DRIVER_MODULE_NAME := wlan
WIFI_DRIVER_MODULE_ARG :=
''')
path = device/'manifest.xml'
manifest = ET.parse(path)
root = manifest.getroot()
specs = [('android.hardware.wifi','1.3','IWifi'),
         ('android.hardware.wifi.supplicant','1.2','ISupplicant'),
         ('android.hardware.wifi.hostapd','1.1','IHostapd'),
         ('android.hardware.gnss','1.0','IGnss'),
         ('android.hardware.memtrack','1.0','IMemtrack')]
for name,version,interface in specs:
    if any(h.findtext('name')==name for h in root.findall('hal')):
        continue
    hal = ET.SubElement(root,'hal',format='hidl')
    ET.SubElement(hal,'name').text=name
    ET.SubElement(hal,'transport').text='hwbinder'
    ET.SubElement(hal,'version').text=version
    iface = ET.SubElement(hal,'interface')
    ET.SubElement(iface,'name').text=interface
    ET.SubElement(iface,'instance').text='default'
ET.indent(manifest)
manifest.write(path,encoding='utf-8',xml_declaration=True)
report={'source_commit':subprocess.check_output(['git','-C',str(source.parent),'rev-parse','HEAD'],text=True).strip(),
        'source_driver_version':'3.8.22.14', 'checked_kernel_crcs':audit[0]['checked_import_crcs'],
        'packaged_module_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'packaged_module_bytes':target.stat().st_size,'force_load':False,'runtime_verified':False}
(host/'android10-wifi-staging.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
