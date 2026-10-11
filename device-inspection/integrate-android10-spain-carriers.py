"""Device-local Spanish APNs and explicit modem preference utility; no device writes."""
from pathlib import Path
import xml.etree.ElementTree as ET
import json, hashlib, subprocess, shutil

workspace = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
tree = Path('/home/pablo/kyf37-android10')
device = tree / 'device/kyocera/kyf37'
assert subprocess.run(['pgrep', '-x', 'ninja'], stdout=subprocess.DEVNULL).returncode != 0
base = tree / 'vendor/lineage/prebuilt/common/etc/apns-conf.xml'
root = ET.parse(base).getroot()
changed = []
for e in root:
    if e.get('mcc') != '214': continue
    if e.get('mnc') == '01' and e.get('carrier') == 'Vodafone ES':
        e.set('user', ''); e.set('password', ''); e.set('authtype', '1')
        e.set('protocol', 'IP'); e.set('roaming_protocol', 'IP')
        changed.append(dict(e.attrib))
    if e.get('mnc') == '07' and e.get('carrier') == 'Movistar':
        # Keep the established telefonica.es credentials for the combined MMS profile.
        e.set('mmsproxy', '10.138.255.5'); e.set('port', '')
        changed.append(dict(e.attrib))
    if e.get('mnc') == '22' and e.get('apn') == 'internet.digimobil.es':
        # Own MCC/MNC identifies DIGI; an SPN restriction excludes otherwise valid SIMs.
        e.attrib.pop('mvno_type', None); e.attrib.pop('mvno_match_data', None)
        e.set('user', ''); e.set('password', ''); e.set('authtype', '0')
        changed.append(dict(e.attrib))

def add(**attributes):
    if not any(all(e.get(k) == v for k, v in attributes.items()) for e in root):
        ET.SubElement(root, 'apn', attributes)
    changed.append(attributes)

add(carrier='Movistar ES Internet', mcc='214', mnc='07', apn='movistar.es',
    user='MOVISTAR', password='MOVISTAR', authtype='1', type='default,supl')
# Vodafone's IMS profile already exists in the base. DIGI's values are in the
# current Lineage APN database; Orange/Movistar are explicit bring-up profiles,
# not claims that their modem provisioning/registration has passed.
for carrier, mnc in [('Vodafone ES', '01'), ('Orange ES', '03'),
                     ('Movistar ES', '07'), ('DIGI Spain', '22')]:
    old = [e for e in root if e.get('mcc') == '214' and e.get('mnc') == mnc
           and e.get('type') == 'ims' and not e.get('mvno_type')]
    for e in old: root.remove(e)
    add(carrier=carrier+' IMS', mcc='214', mnc=mnc, apn='ims', type='ims',
        protocol='IPV4V6', roaming_protocol='IPV4V6', user_visible='false')

ET.indent(root, space='  ')
apns = device / 'apns-conf.xml'
ET.ElementTree(root).write(apns, encoding='utf-8', xml_declaration=True)
# Preserve original copyright/license header from the inherited database.
text = apns.read_text()
start = base.read_text().find('<!--'); end = base.read_text().find('-->', start)
if start >= 0:
    text = text.replace('<apns ', base.read_text()[start:end+3]+'\n<apns ', 1)
apns.write_text(text+'\n')
mk = device / 'lineage.mk'
line = 'PRODUCT_COPY_FILES := device/kyocera/kyf37/apns-conf.xml:system/etc/apns-conf.xml $(PRODUCT_COPY_FILES)\n'
if line not in mk.read_text(): mk.write_text(mk.read_text()+'\n# Device-specific Spanish carrier defaults take precedence.\n'+line)

radio = device / 'radio-tools'; radio.mkdir(exist_ok=True)
source = (workspace/'device-inspection/kyf37_qmux.c').read_text()
source = source.replace('/* NAS read through the firmware\'s QMUX daemon; no radio configuration writes. */',
    '/* KYF37 QMUX NAS reader; LTE write occurs only with explicit --enable-spain. */')
source = source.replace('setbuf(stdout,NULL);',
    'if (argc > 2 || (argc == 2 && strcmp(argv[1], "--enable-spain"))) { fputs("Usage: kyf37_qmux [--enable-spain]\\n", stderr); return 1; }\n setbuf(stdout,NULL);')
source = source.replace('if(mask!=0x02000001ULL)',
    'if(mask==0x0a0800c5ULL){puts("Spain LTE preference already present; no write");close(fd);return 0;}\n   if(mask!=0x02000001ULL)')
# A failed QMI result must not be mistaken for a valid LTE mask.
source = source.replace('if(type==0x15&&len==8)',
    'if(type==0x02&&len==4&&(p[i]||p[i+1]||p[i+2]||p[i+3]))return 0;\n if(type==0x15&&len==8)')
(radio/'kyf37_qmux.c').write_text(source)
(radio/'Android.bp').write_text('cc_binary {\n    name: "kyf37_qmux",\n    srcs: ["kyf37_qmux.c"],\n    cflags: ["-Wall"],\n}\n')
package = 'PRODUCT_PACKAGES += kyf37_qmux\n'
if package not in mk.read_text(): mk.write_text(mk.read_text()+package)

report = {
    'profiles': changed,
    'apns_sha256': hashlib.sha256(apns.read_bytes()).hexdigest(),
    'sources': [
        'https://ayuda.orange.es/particulares/movil/mi-movil/configurar/1061-configura-el-apn-para-una-sim-de-orange',
        'https://www.digimobil.es/configurar-internet',
        'https://ayudacliente.vodafone.es/particulares/movil/tu-dispositivo/como-configurar-el-apn-en-el-movil/',
        'https://comunidad.movistar.es/discussions/ayuda_tecnica_movil/configuraci%C3%B3n-de-apn-en-android/1064268',
        'https://github.com/LineageOS/android_vendor_apn/blob/main/ES.xml'],
    'ims': {'apn_profiles_added': True, 'registration_verified': False,
            'stock_interface': 'Android 5 com.android.ims.internal.IImsService$Stub',
            'android10_vendor_service_port_complete': False,
            'experimental_profiles': ['Orange ES IMS', 'Movistar ES IMS']},
    'lte': {'desired_mask': '0x0a0800c5', 'bands': [1,3,7,8,20,26,28],
            'previous_reboot_readback_verified': True,
            'post_stock_restoration_readback_verified': False,
            'hardware_reception_verified': False,
            'automatic_modem_writes': False,
            'utility': '/system/bin/kyf37_qmux [--enable-spain]'},
    'hardware_tested': False,
}
(device/'spain-carriers.json').write_text(json.dumps(report, indent=2)+'\n')
(workspace/'kyf37-rom/android10-spain-carriers.json').write_text(json.dumps(report, indent=2)+'\n')
shutil.copy2(apns, workspace/'kyf37-rom/apns-conf-spain.xml')
print(json.dumps(report, indent=2))
