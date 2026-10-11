"""Translate the exact stock policy to Android 10 XML; report OEM-only enums."""
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

tree = Path('/home/pablo/kyf37-android10')
device = tree / 'device/kyocera/kyf37'
source = Path('/home/pablo/kyf37-rom/stock-system/etc/audio_policy.conf')
text = re.sub(r'/\*.*?\*/', '', source.read_text(), flags=re.S)
text = re.sub(r'#.*', '', text)
tokens = iter(re.findall(r'[^\s{}]+|[{}]', text))
def parse():
    result = {}
    for name in tokens:
        if name == '}':
            return result
        value = next(tokens)
        result[name] = parse() if value == '{' else value
    return result
conf = parse()
headers = '\n'.join(p.read_text() for p in (tree/'system/media/audio/include/system').glob('*.h'))
known = set(re.findall(r'\bAUDIO_[A-Z0-9_]+\b', headers))
omitted = set()
def values(value):
    result = []
    for item in value.split('|'):
        if item.startswith('AUDIO_') and item not in known:
            omitted.add(item)
        elif item != 'dynamic':
            result.append(item)
    return result
root = ET.Element('audioPolicyConfiguration', version='1.0', attrib={'xmlns:xi':'http://www.w3.org/2001/XInclude'})
ET.SubElement(root, 'globalConfiguration', speaker_drc_enabled='true')
modules = ET.SubElement(root, 'modules')
primary = conf['audio_hw_modules']['primary']
module = ET.SubElement(modules, 'module', name='primary', halVersion='2.0')
attached = ET.SubElement(module, 'attachedDevices')
ET.SubElement(module, 'defaultOutputDevice').text = 'AUDIO_DEVICE_OUT_SPEAKER'
mixes = ET.SubElement(module, 'mixPorts')
ports = ET.SubElement(module, 'devicePorts')
routes = ET.SubElement(module, 'routes')
devices = {}
for direction, role in [('outputs','source'), ('inputs','sink')]:
    for name, profile in primary[direction].items():
        mixname = name + ' ' + direction
        attrs = {'name':mixname, 'role':role}
        flags = values(profile.get('flags',''))
        if flags and flags != ['']:
            attrs['flags'] = '|'.join(flags)
        mix = ET.SubElement(mixes, 'mixPort', **attrs)
        for fmt in values(profile['formats']):
            ET.SubElement(mix,'profile', name='', format=fmt,
                          samplingRates=','.join(values(profile['sampling_rates'])),
                          channelMasks=','.join(values(profile['channel_masks'])))
        for dev in values(profile['devices']):
            # ALL_* masks are not device ports; expand their defined members.
            if '_ALL_' in dev:
                suffix = dev.split('_ALL_')[1]
                prefix = 'AUDIO_DEVICE_OUT_'
                members = [d for d in known if d.startswith(prefix) and '_ALL_' not in d and suffix in d]
            else:
                members = [dev]
            for member in sorted(members):
                devices.setdefault(member, (role, []))[1].append(mixname)
for dev, (role, names) in sorted(devices.items()):
    ET.SubElement(ports, 'devicePort', tagName=dev, type=dev, role='sink' if role=='source' else 'source')
    if role == 'source':
        ET.SubElement(routes, 'route', type='mix', sink=dev, sources=','.join(names))
    else:
        for name in names:
            # Each input stream has one route collecting its supported devices.
            pass
for mix in mixes:
    if mix.attrib['role'] == 'sink':
        sources = [d for d, (r,names) in devices.items() if mix.attrib['name'] in names]
        ET.SubElement(routes,'route',type='mix',sink=mix.attrib['name'],sources=','.join(sorted(sources)))
global_conf = conf['global_configuration']
for field in ['attached_output_devices','attached_input_devices']:
    for dev in values(global_conf[field]):
        if dev in devices:
            ET.SubElement(attached,'item').text = dev
for name in ['a2dp_audio_policy_configuration.xml','usb_audio_policy_configuration.xml','r_submix_audio_policy_configuration.xml']:
    ET.SubElement(modules,'xi:include',href=name)
for name in ['audio_policy_volumes.xml','default_volume_tables.xml']:
    ET.SubElement(root,'xi:include',href=name)
ET.indent(root)
ET.ElementTree(root).write(device/'audio_policy_configuration.xml', encoding='utf-8',xml_declaration=True)
board = device/'BoardConfig.mk'
if 'USE_XML_AUDIO_POLICY_CONF := 1' not in board.read_text():
    board.write_text(board.read_text()+'\nUSE_XML_AUDIO_POLICY_CONF := 1\n')
vendor = tree/'vendor/kyocera/kyf37/kyf37-vendor.mk'
vendor.write_text(re.sub(r'\s+vendor/kyocera/kyf37/proprietary/etc/audio_policy.conf:\S+', '', vendor.read_text()))
mk = device/'device.mk'
marker = '# Android 10 XML audio policy'
if marker not in mk.read_text():
    entries = ['device/kyocera/kyf37/audio_policy_configuration.xml:system/etc/audio_policy_configuration.xml']
    for name in ['a2dp_audio_policy_configuration.xml','usb_audio_policy_configuration.xml','r_submix_audio_policy_configuration.xml','audio_policy_volumes.xml','default_volume_tables.xml']:
        entries.append('frameworks/av/services/audiopolicy/config/'+name+':system/etc/'+name)
    mk.write_text(mk.read_text()+'\n'+marker+'\nPRODUCT_COPY_FILES += '+ ' '.join(entries)+'\n')
report = {'source':str(source), 'omitted_oem_enums': sorted(omitted), 'runtime_verified':False}
(device/'audio-policy-port.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
