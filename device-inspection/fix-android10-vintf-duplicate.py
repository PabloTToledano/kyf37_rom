from pathlib import Path
import xml.etree.ElementTree as ET,subprocess
r=Path('/home/pablo/kyf37-android10');p=r/'device/kyocera/kyf37/manifest.xml'
tree=ET.parse(p);root=tree.getroot();items=[h for h in root.findall('hal') if h.findtext('name')=='android.hardware.cas'];assert len(items)==1
root.remove(items[0]);ET.indent(tree,space='  ');tree.write(p,encoding='utf-8',xml_declaration=True)
fragment=r/'out/target/product/kyf37/system/vendor/etc/vintf/manifest/android.hardware.cas@1.1-service.xml'
output=Path('/home/pablo/kyf37-rom/v6-merged-device-manifest.xml')
subprocess.run([str(r/'out/host/linux-x86/bin/assemble_vintf'),'-i',str(p)+':'+str(fragment),'-o',str(output)],check=True)
t=ET.parse(output);names=[h.findtext('name') for h in t.getroot().findall('hal')]
assert names.count('android.hardware.cas')==1 and 'android.hardware.graphics.composer' in names
print('Corrected manifest merges with packaged fragment successfully')
