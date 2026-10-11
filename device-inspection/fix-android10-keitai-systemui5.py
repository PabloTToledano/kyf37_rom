"""Keitai pass 5: shade header count refreshes every second (first draw precedes row layout)."""
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI/src/com/android/systemui/statusbar/phone/Kyf37KeitaiShadeHeader.java')
s = p.read_text().replace('postDelayed(this, 5000)', 'postDelayed(this, 1000)')
assert 'postDelayed(this, 1000)' in s
p.write_text(s)
print('Keitai SystemUI pass 5 staged')
