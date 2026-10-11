#!/usr/bin/env python3
"""Make the KYF37 lid sleep the internal display by default.

SettingsProvider seeds lid_behavior=1 from config_lidControlsSleep on clean
data. Existing phones need settings put global lid_behavior 1 (no data wipe).
Stock open.mp3/close.mp3 are already loaded by Kyf37Feedback; enable their
existing settings on the device with apply-lid-sleep.ps1.
"""
from pathlib import Path
root = Path.home() / 'kyf37-android10'
p = root / 'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_lid.xml'
p.parent.mkdir(parents=True, exist_ok=True)
s = p.read_text() if p.exists() else '<resources>\n</resources>\n'
import re
entry = '<bool name="config_lidControlsSleep">true</bool>'
if 'name="config_lidControlsSleep"' in s:
    s = re.sub(r'<bool name="config_lidControlsSleep">.*?</bool>', entry, s)
else:
    s = s.replace('</resources>', '    ' + entry + '\n</resources>')
p.write_text(s)
print('Default lid behavior: internal display sleeps on close; existing wake-on-open policy retained')
