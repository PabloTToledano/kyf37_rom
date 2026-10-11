#!/usr/bin/env python3
"""Idempotent: replace LineageOS's teal system accent (#167C80) with a clear blue (owner: 'I dont like the green color,
it should be a nice blue'). One accent drives QS active tiles, sliders, switches, links and buttons in SystemUI, Settings,
dialogs and our apps. Lineage defines it in vendor/lineage/overlay/common/.../colors.xml; our device overlay
(DEVICE_PACKAGE_OVERLAYS in BoardConfig.mk) is applied on top, so we redefine the same names there. SetupWizard keeps its own
copy of the teal, patched in place.
Palette: light #1E6FD9 (nice medium blue, readable on white), dark #7AB0F7, 700 #1555B0.
Run in WSL; takes effect with the next framework-res / SystemUI / Settings / SetupWizard build."""
import pathlib, re
T = pathlib.Path.home() / 'kyf37-android10'
OV = T / 'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values'
OV.mkdir(parents=True, exist_ok=True)
LIGHT, DARK, D700 = '#1E6FD9', '#7AB0F7', '#1555B0'
xml = f'''<?xml version="1.0" encoding="utf-8"?>
<!-- KYF37: blue system accent instead of Lineage teal (fix-android10-accent-blue.py) -->
<resources>
    <color name="accent_device_default_700">{D700}</color>
    <color name="accent_device_default_dark">{DARK}</color>
    <color name="accent_device_default_light">{LIGHT}</color>
    <color name="material_deep_teal_200">{DARK}</color>
    <color name="material_deep_teal_500">{LIGHT}</color>
</resources>
'''
f = OV / 'kyf37_accent.xml'
if not f.exists() or f.read_text() != xml:
    f.write_text(xml, newline='\n'); print('wrote', f)
else:
    print('overlay up to date')
sw = T / 'packages/apps/SetupWizard/res/values/colors.xml'
if sw.exists():
    t = sw.read_text()
    n = re.sub(r'#(ff)?167C80', LIGHT, t, flags=re.I)
    if n != t:
        sw.write_text(n, newline='\n'); print('patched SetupWizard colors')
    else:
        print('SetupWizard colors already blue')

# The device overlay alone does NOT win over Lineage's overlay in this tree (verified: framework-res kept #167c80),
# so also patch Lineage's own colour file in place (same names, blue values).
lin = T / 'vendor/lineage/overlay/common/frameworks/base/core/res/res/values/colors.xml'
if lin.exists():
    t = lin.read_text()
    want = {'accent_device_default_700': D700, 'accent_device_default_dark': DARK, 'accent_device_default_light': LIGHT,
            'material_deep_teal_200': DARK, 'material_deep_teal_500': LIGHT}
    n = t
    for name, val in want.items():
        n = re.sub(r'(<color name="%s">)#[0-9A-Fa-f]{6,8}(</color>)' % name, r'\g<1>%s\g<2>' % val, n)
    if n != t:
        lin.write_text(n, newline=chr(10)); print('patched Lineage overlay colors.xml')
    else:
        print('Lineage overlay colors already blue')
print('done')
