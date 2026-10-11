from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java')
s=p.read_text()
a='''        // An open KYF37 must wake from its physical keypad.'''
b='''        // With the lid open and the device unlocked the side key toggles the notification shade.
        if (mKyf37Navigation != null && !isInjected
                && keyCode == KeyEvent.KEYCODE_CAMERA
                && mDefaultDisplayPolicy.getLidState() != LID_CLOSED
                && interactive && !keyguardActive) {
            if (down && event.getRepeatCount() == 0) {
                mHandler.post(new Runnable() { public void run() {
                    try {
                        IStatusBarService sb = getStatusBarService();
                        if (sb != null) sb.togglePanel();
                    } catch (RemoteException e) { }
                }});
            }
            return 0;
        }

'''
if 'side key toggles the notification shade' not in s:
    assert s.count(a)==1
    s=s.replace(a,b+a); p.write_text(s)
print('ok')
