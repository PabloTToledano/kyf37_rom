from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
p=root/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
# Keep ending calls, but never let the red key put this device to sleep.
s=s.replace('''if ((mEndcallBehavior
                                    & Settings.System.END_BUTTON_BEHAVIOR_SLEEP) != 0)''', '''if (mKyf37Navigation == null && (mEndcallBehavior
                                    & Settings.System.END_BUTTON_BEHAVIOR_SLEEP) != 0)''')
a='''        // Basic policy based on interactive state.
'''
b='''        if (mKyf37Navigation != null && !isInjected && event.getScanCode() > 0) {
            final int mappedCode = Settings.Secure.getIntForUser(mContext.getContentResolver(),
                    "kyf37_key_" + event.getScanCode(), keyCode, mCurrentUserId);
            if (mappedCode > 0 && mappedCode != keyCode && mappedCode <= KeyEvent.getMaxKeyCode()) {
                final KeyEvent mapped = new KeyEvent(event.getDownTime(), event.getEventTime(),
                        event.getAction(), mappedCode, event.getRepeatCount(), event.getMetaState(),
                        -1, event.getScanCode(), event.getFlags(), event.getSource());
                mHandler.post(new Runnable() { public void run() {
                    try { InputManager.getInstance().injectInputEvent(mapped,
                            InputManager.INJECT_INPUT_EVENT_MODE_ASYNC); }
                    finally { mapped.recycle(); }
                }});
                return 0;
            }
        }

'''
if '"kyf37_key_" + event.getScanCode()' not in s:
 assert s.count(a)==1
 s=s.replace(a,b+a)
p.write_text(s)
# The footer must actually have a navigation window on this physical-key device.
p=root/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_softkey_dimensions.xml'
s=p.read_text()
if 'config_showNavigationBar' not in s:s=s.replace('<resources>','<resources>\n    <bool name="config_showNavigationBar">true</bool>')
p.write_text(s)
p=root/'frameworks/base/core/res/AndroidManifest.xml'
s=p.read_text()
if 'org.kyf37.POINTER_CHANGED' not in s:s=s.replace('<protected-broadcast android:name="android.intent.action.BOOT_COMPLETED" />','<protected-broadcast android:name="android.intent.action.BOOT_COMPLETED" />\n    <protected-broadcast android:name="org.kyf37.POINTER_CHANGED" />')
p.write_text(s)
# Latest request: clock stays on whenever the lid is closed.
p=root/'packages/apps/Kyf37OuterScreen/src/org/kyf37/subdisplay/OuterScreenService.java'
s=p.read_text().replace('boolean visible=closed && elapsed<visibleUntil;', 'boolean visible=closed;')
s=s.replace('if(visible) handler.postDelayed(blank,visibleUntil-elapsed);','// The closed-lid clock is refreshed by the minute wakeup alarm below.')
p.write_text(s)
p=root/'device/kyocera/kyf37/device.mk'
s=p.read_text()
if 'PRODUCT_PACKAGES += Camera2 Kyf37KeypadSettings' not in s:s+='\nPRODUCT_PACKAGES += Camera2 Kyf37KeypadSettings\n'
p.write_text(s)
print('Key remapping, red-key no-sleep policy, visible footer, camera and closed-lid clock source updated')
