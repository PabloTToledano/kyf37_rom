from pathlib import Path
tree=Path('/home/pablo/kyf37-android10')
device=tree/'device/kyocera/kyf37'
p=device/'device.mk';s=p.read_text()
entry='PRODUCT_PACKAGES += android.hardware.keymaster@3.0-service android.hardware.keymaster@3.0-impl'
if entry not in s:s+='\n'+entry+'\n'
p.write_text(s)
import xml.etree.ElementTree as ET
p=device/'manifest.xml';doc=ET.parse(p);root=doc.getroot()
if not any(hal.findtext('name')=='android.hardware.keymaster' for hal in root.findall('hal')):
 hal=ET.SubElement(root,'hal',{'format':'hidl'})
 ET.SubElement(hal,'name').text='android.hardware.keymaster'
 ET.SubElement(hal,'transport').text='hwbinder'
 ET.SubElement(hal,'version').text='3.0'
 interface=ET.SubElement(hal,'interface');ET.SubElement(interface,'name').text='IKeymasterDevice';ET.SubElement(interface,'instance').text='default'
 ET.indent(root);doc.write(p,encoding='utf-8',xml_declaration=True)
print('Selected platform keymaster3 legacy/software wrapper')
