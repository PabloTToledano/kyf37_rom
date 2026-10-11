"""Apply the owner's F3 pointer mapping and physical-key wake policy."""
from pathlib import Path
import re

tree=Path('/home/pablo/kyf37-android10')
policy=tree/'frameworks/base/services/core/java/com/android/server/policy'
nav=policy/'Kyf37Navigation.java'
text=nav.read_text()
text=text.replace('F4 toggles a cursor','F3 toggles a cursor')
text=text.replace('''        if (nativeKeys) {
            if (enabled) reset();
            return false;
        }
''','')
text=text.replace('if (code == KeyEvent.KEYCODE_F2) {','if (code == KeyEvent.KEYCODE_F2 && !nativeKeys) {')
text=text.replace('if (code == KeyEvent.KEYCODE_F4) {','if (code == KeyEvent.KEYCODE_F3) {')
text=text.replace('F4 exits','F3 exits')
nav.write_text(text)
pwm=policy/'PhoneWindowManager.java'
text=pwm.read_text()
old='event.getKeyCode() == KeyEvent.KEYCODE_F3 && !kyf37NativeKeys'
if old in text:
    text=text.replace(old,'event.getKeyCode() == KeyEvent.KEYCODE_F4 && !kyf37NativeKeys')
anchor='''        // Basic policy based on interactive state.
'''
addition='''        // An open KYF37 must wake from its physical keypad. Consume the waking
        // press instead of letting it accidentally activate a sleeping app.
        if (mKyf37Navigation != null && !interactive && !isInjected && down
                && event.getDeviceId() >= 0
                && mDefaultDisplayPolicy.getLidState() != LID_CLOSED) {
            wakeUp(event.getEventTime(), mAllowTheaterModeWakeFromKey,
                    PowerManager.WAKE_REASON_WAKE_KEY, "android.policy:KYF37_KEY", true);
            mPendingWakeKey = keyCode;
            return 0;
        }

'''
if 'android.policy:KYF37_KEY' not in text:
    assert text.count(anchor)==1
    text=text.replace(anchor,addition+anchor)
pwm.write_text(text)
layout=tree/'device/kyocera/kyf37/keylayout/matrix_keypad_67.kl'
lines=[]
for line in layout.read_text().splitlines():
    if re.match(r'^key\s+\d+\s+\w+\s*$',line):
        line=line.rstrip()+' WAKE'
    lines.append(line)
layout.write_text('\n'.join(lines)+'\n')
home=tree/'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
text=home.read_text().replace('F4: cursor','F3: cursor')
text=text.replace('F2: Menu  F3: Home  F4: Cursor','F2: Menu  F3: Cursor  F4: Home')
text=text.replace('KYF37\\nArrows: move  Center: open\\nCall: phone  Menu: settings  F3: cursor','Applications')
start=text.find('        TextView guide = new TextView(this);')
end=text.find('        setContentView(screen);',start)
if start>=0:
    assert end>start
    text=text[:start]+text[end:]
home.write_text(text)
print('F3 toggles pointer globally; disabled pointer passes D-pad; physical keys wake open phone')
