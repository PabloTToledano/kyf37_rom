"""KYF37 keypad-nav: Settings homepage rows were unreachable by D-pad (a blocksDescendants container kept the
ScrollView focused and Up/Down only scrolled). Remove it so the first row takes focus. Idempotent; WSL Python 3."""
from pathlib import Path
p = Path('/home/pablo/kyf37-android10/packages/apps/Settings/res/layout/settings_homepage_container.xml')
s = p.read_text()
n = s.replace('\n            android:descendantFocusability="blocksDescendants">', '>')
if n != s:
    p.write_text(n)
    print('patched', p.name)
