from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/Kyf37Navigation.java')
s=p.read_text()
s=s.replace('final boolean down = event.getAction() == KeyEvent.ACTION_DOWN;', 'final boolean down = event.getAction() == KeyEvent.ACTION_DOWN;\n        final boolean select = code == KeyEvent.KEYCODE_DPAD_CENTER\n                || code == KeyEvent.KEYCODE_ENTER || code == KeyEvent.KEYCODE_NUMPAD_ENTER;')
s=s.replace('&& code != KeyEvent.KEYCODE_DPAD_CENTER) return false;', '&& !select) return false;')
s=s.replace('if (code == KeyEvent.KEYCODE_DPAD_CENTER) {', 'if (select) {')
p.write_text(s)
print('Pointer mode now accepts physical ENTER center key; D-pad mode unchanged')
