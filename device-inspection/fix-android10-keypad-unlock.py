from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI/src/com/android/systemui/statusbar/phone/StatusBarWindowView.java')
s=p.read_text()
a='''        if (super.dispatchKeyEvent(event)) {
'''
b='''        // Physical Select opens the normal keyguard bouncer on the KYF37.
        // PIN/password authentication remains owned by Keyguard.
        if (android.os.Build.DEVICE.equals("kyf37")
                && (event.getKeyCode() == KeyEvent.KEYCODE_DPAD_CENTER
                    || event.getKeyCode() == KeyEvent.KEYCODE_ENTER)
                && mStatusBarStateController.getState() == com.android.systemui.statusbar.StatusBarState.KEYGUARD
                && !mService.isBouncerShowing()) {
            if (event.getAction() == KeyEvent.ACTION_UP
                    && mService.onSpacePressed()) {
                return true;
            }
        }
'''
# Use existing imports/state accessor only after checking source.
assert s.count(a)==1
if 'Physical Select opens the normal keyguard' not in s:
 s=s.replace(a,b+a)
 p.write_text(s)
print('Keypad keyguard entry added; existing authentication preserved')
