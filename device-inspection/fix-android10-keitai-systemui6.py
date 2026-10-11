"""Keitai pass 6: no layout background behind the shade guide (it draws its own when unlocked)."""
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI/res/layout/status_bar_expanded.xml')
s = p.read_text()
s = s.replace('        android:background="#F0142638"\n', '')
assert 'F0142638' not in s
p.write_text(s)
print('Keitai SystemUI pass 6 staged')
