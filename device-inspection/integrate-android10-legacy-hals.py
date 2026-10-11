from pathlib import Path
import xml.etree.ElementTree as ET
tree=Path('/home/pablo/kyf37-android10')
device=tree/'device/kyocera/kyf37'
packages=[
 'android.hardware.audio@2.0-service', 'android.hardware.audio@2.0-impl',
 'android.hardware.audio.effect@2.0-impl',
 'android.hardware.bluetooth@1.0-service','android.hardware.bluetooth@1.0-impl',
 'android.hardware.camera.provider@2.4-service','android.hardware.camera.provider@2.4-impl',
 'android.hardware.graphics.allocator@2.0-service','android.hardware.graphics.allocator@2.0-impl',
 'android.hardware.graphics.mapper@2.0-impl',
 'android.hardware.graphics.composer@2.1-service','android.hardware.graphics.composer@2.1-impl',
 'android.hardware.light@2.0-service','android.hardware.light@2.0-impl',
 'android.hardware.power@1.0-service','android.hardware.power@1.0-impl',
 'android.hardware.sensors@1.0-service','android.hardware.sensors@1.0-impl',
 'android.hardware.vibrator@1.0-service','android.hardware.vibrator@1.0-impl',
 'rild','libxml2',
]
path=device/'device.mk'
text=path.read_text()
marker='# Android10 legacy HAL wrappers'
assert marker not in text, 'Already integrated; review before regenerating'
path.write_text(text+'\n'+marker+'\nPRODUCT_PACKAGES += '+' '.join(packages)+'\n')
manifest=ET.Element('manifest',{'version':'1.0','type':'device','target-level':'2'})
interfaces=[
 ('audio','2.0','IDevicesFactory','default','hwbinder'),
 ('audio.effect','2.0','IEffectsFactory','default','hwbinder'),
 ('bluetooth','1.0','IBluetoothHci','default','hwbinder'),
 ('camera.provider','2.4','ICameraProvider','legacy/0','hwbinder'),
 ('graphics.allocator','2.0','IAllocator','default','hwbinder'),
 ('graphics.mapper','2.0','IMapper','default','passthrough'),
 ('graphics.composer','2.1','IComposer','default','hwbinder'),
 ('light','2.0','ILight','default','hwbinder'),
 ('power','1.0','IPower','default','hwbinder'),
 ('sensors','1.0','ISensors','default','hwbinder'),
 ('vibrator','1.0','IVibrator','default','hwbinder'),
 ('radio','1.0','IRadio','slot1','hwbinder'),
]
for name,version,interface,instance,transport in interfaces:
 hal=ET.SubElement(manifest,'hal',{'format':'hidl'})
 ET.SubElement(hal,'name').text='android.hardware.'+name
 attributes={'arch':'32'} if transport=='passthrough' else {}
 ET.SubElement(hal,'transport',attributes).text=transport
 ET.SubElement(hal,'version').text=version
 entry=ET.SubElement(hal,'interface');ET.SubElement(entry,'name').text=interface;ET.SubElement(entry,'instance').text=instance
ET.indent(manifest)
ET.ElementTree(manifest).write(device/'manifest.xml',encoding='utf-8',xml_declaration=True)
board=device/'BoardConfig.mk'
text=board.read_text().replace('BOARD_VNDK_VERSION := current','BOARD_VNDK_VERSION :=')
board.write_text(text+'\nDEVICE_MANIFEST_FILE := device/kyocera/kyf37/manifest.xml\n')
print('Declared',len(interfaces),'legacy wrapped HAL interfaces; runtime compatibility unverified')
