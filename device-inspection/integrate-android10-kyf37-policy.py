from pathlib import Path
import shutil
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
tree=Path('/home/pablo/kyf37-android10')
p=tree/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
assert '// KYF37 Android10 integration' not in s
pairs=[
 ('    Context mContext;','    Context mContext;\n    // KYF37 Android10 integration\n    Kyf37Navigation mKyf37Navigation;\n    Kyf37Feedback mKyf37Feedback;'),
 ('        mHandler = new PolicyHandler();','''        mHandler = new PolicyHandler();
        if (SystemProperties.getBoolean("ro.kyf37.keypad_navigation", false)) {
            mKyf37Navigation = new Kyf37Navigation(context, mHandler);
            mKyf37Feedback = new Kyf37Feedback(context, mHandler);
            mKyf37Feedback.userChanged(UserHandle.USER_SYSTEM);
        }'''),
 ('    public void setCurrentUserLw(int newUserId) {','''    public void setCurrentUserLw(int newUserId) {
        if (mKyf37Navigation != null) mKyf37Navigation.reset();
        if (mKyf37Feedback != null) mKyf37Feedback.userChanged(newUserId);'''),
 ('    public void finishedGoingToSleep(int why) {','    public void finishedGoingToSleep(int why) {\n        if (mKyf37Navigation != null) mKyf37Navigation.reset();'),
 ('        final boolean interactive = (policyFlags & FLAG_INTERACTIVE) != 0;','''        final boolean interactive = (policyFlags & FLAG_INTERACTIVE) != 0;
        if (mKyf37Feedback != null && (policyFlags & FLAG_INJECTED) == 0)
            mKyf37Feedback.key(event, interactive);'''),
 ('        mDefaultDisplayPolicy.setLidState(newLidState);','''        mDefaultDisplayPolicy.setLidState(newLidState);
        if (!lidOpen && mKyf37Navigation != null) mKyf37Navigation.reset();
        if (mKyf37Feedback != null) mKyf37Feedback.lidChanged(lidOpen);
        publishKyf37LidState();'''),
 ('        mDefaultDisplayPolicy.setLidState(mWindowManagerFuncs.getLidState());','        mDefaultDisplayPolicy.setLidState(mWindowManagerFuncs.getLidState());\n        publishKyf37LidState();'),
]
for old,new in pairs:
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
anchor=s.index('    private long interceptKeyBeforeDispatchingInner(')
tail=s[anchor:]
old='        final int keyCode = event.getKeyCode();'
new='''        final boolean kyf37NativeKeys = !keyguardOn && win != null
                && "jp.kyocera.afphome".equals(win.getOwningPackage());
        if (mKyf37Navigation != null
                && mKyf37Navigation.intercept(event, kyf37NativeKeys)) return -1;
        final int keyCode = event.getKeyCode() == KeyEvent.KEYCODE_F3 && !kyf37NativeKeys
                ? KeyEvent.KEYCODE_HOME : event.getKeyCode();'''
assert old in tail
s=s[:anchor]+tail.replace(old,new,1)
helper='''    private void publishKyf37LidState() {
        if (!SystemProperties.getBoolean("ro.kyf37.outer_screen", false)) return;
        final String state = mDefaultDisplayPolicy.getLidState() == LID_CLOSED ? "false" : "true";
        if (state.equals(SystemProperties.get("sys.kyf37.lid_open"))) return;
        SystemProperties.set("sys.kyf37.lid_open", state);
        if (!SystemProperties.getBoolean("sys.boot_completed", false)) return;
        mHandler.post(new Runnable() { public void run() {
            Intent service = new Intent();
            service.setComponent(new ComponentName("org.kyf37.subdisplay", "org.kyf37.subdisplay.OuterScreenService"));
            mContext.startServiceAsUser(service, UserHandle.SYSTEM);
        }});
    }

'''
s=s.replace('    void readLidState() {',helper+'    void readLidState() {')
p.write_text(s)
shutil.copy2(host/'kyf37-rom/kyocera-compat/policy-source/Kyf37Navigation.java',p.parent/'Kyf37Navigation.java')
shutil.copy2(host/'kyf37-rom/navigation/Kyf37Feedback.java',p.parent/'Kyf37Feedback.java')
for name,target in [('ime','packages/inputmethods/Kyf37KeypadIME'),('home','packages/apps/Kyf37Home'),('subdisplay','packages/apps/Kyf37OuterScreen')]:
 shutil.copytree(host/'kyf37-rom/navigation'/name,tree/target,dirs_exist_ok=True)
native=tree/'packages/apps/Kyf37OuterScreen/Android.mk'
native.write_text(native.read_text().replace('LOCAL_C_INCLUDES := libnativehelper/include/nativehelper','LOCAL_HEADER_LIBRARIES := jni_headers'))
layout=tree/'device/kyocera/kyf37/keylayout/matrix_keypad_67.kl'
layout.write_text(layout.read_text().replace('key 61      HOME','key 61      F3'))
print('Integrated Android10 physical keys, OEM feedback, lid and outer-screen sources')
