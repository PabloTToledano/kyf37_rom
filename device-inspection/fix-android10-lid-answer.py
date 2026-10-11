from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java')
s=p.read_text()
a='''        if (lidOpen) {
            wakeUp(SystemClock.uptimeMillis(), mAllowTheaterModeWakeFromLidSwitch,
                    PowerManager.WAKE_REASON_LID, "android.policy:LID");
'''
b='''        if (lidOpen) {
            wakeUp(SystemClock.uptimeMillis(), mAllowTheaterModeWakeFromLidSwitch,
                    PowerManager.WAKE_REASON_LID, "android.policy:LID");
            // Flip phone behaviour: opening the lid answers a ringing call.
            if (mKyf37Navigation != null) {
                mHandler.post(new Runnable() { public void run() {
                    TelecomManager telecom = getTelecommService();
                    if (telecom != null && telecom.isRinging()) telecom.acceptRingingCall();
                }});
            }
'''
if 'opening the lid answers a ringing call' not in s:
    assert s.count(a)==1
    p.write_text(s.replace(a,b))
print('ok')
