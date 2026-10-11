"""Create the keypad-first Phone settings app and make Menu / quick slot 9 open it. WSL; idempotent."""
from pathlib import Path
root = Path('/home/pablo/kyf37-android10')
ws = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection')
app = root / 'packages/apps/Kyf37PhoneSettings'
(app / 'src/org/kyf37/phonesettings').mkdir(parents=True, exist_ok=True)
src = (ws / 'Kyf37PhoneSettings.java.txt').read_text()
src = src.replace('num.setText(String.valueOf((i + 1) % 10));', 'num.setText(i < 10 ? String.valueOf((i + 1) % 10) : "");')
(app / 'src/org/kyf37/phonesettings/PhoneSettings.java').write_text(src)
(app / 'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.phonesettings">
    <uses-sdk android:minSdkVersion="22" android:targetSdkVersion="25" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.BLUETOOTH" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
    <uses-permission android:name="android.permission.WRITE_SETTINGS" />
    <uses-permission android:name="android.permission.ACCESS_NOTIFICATION_POLICY" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    <application android:label="Phone settings" android:allowBackup="false"
            android:theme="@android:style/Theme.Material.NoActionBar">
        <activity android:name="org.kyf37.phonesettings.PhoneSettings" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''')
(app / 'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE_TAGS := optional
LOCAL_PACKAGE_NAME := Kyf37PhoneSettings
LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_CERTIFICATE := platform
LOCAL_SDK_VERSION := current
include $(BUILD_PACKAGE)
''')
dm = root / 'device/kyocera/kyf37/device.mk'
s = dm.read_text()
if 'Kyf37PhoneSettings' not in s:
    dm.write_text(s.rstrip() + '\nPRODUCT_PACKAGES += Kyf37PhoneSettings\n')

# Menu / F1 on the Home grid and quick slot 9 open the new app
h = root / 'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
t = h.read_text()
old = 'launch(new Intent(android.provider.Settings.ACTION_SETTINGS));'
new = 'launch(new Intent(Intent.ACTION_MAIN).setComponent(new android.content.ComponentName("org.kyf37.phonesettings", "org.kyf37.phonesettings.PhoneSettings")));'
t = t.replace(old, new)
h.write_text(t)
q = root / 'frameworks/base/services/core/java/com/android/server/policy/Kyf37QuickKeys.java'
u = q.read_text()
u = u.replace('/*9*/ "settings:" };', '/*9*/ "org.kyf37.phonesettings" };')
q.write_text(u)
print('phone settings app installed into tree')
