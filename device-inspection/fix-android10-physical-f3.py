from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
p=root/'device/kyocera/kyf37/keylayout/matrix_keypad_67.kl'
s=p.read_text().replace('key 65      F12 WAKE','key 65      F3 WAKE')
p.write_text(s)
p=root/'packages/apps/Kyf37KeypadSettings/src/org/kyf37/keypad/KeypadSettings.java'
s=p.read_text().replace('187,141,142,4,5,6','187,141,133,4,5,6').replace('"F3","F4"','"Auxiliary key scan 61","F4"').replace('"Extra key F7"','"F3 (marked pointer key)"')
p.write_text(s)
print('Physical F3 scancode 65 mapped to Android F3; settings defaults aligned')
