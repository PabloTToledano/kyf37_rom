#!/usr/bin/env python3
"""Idempotent: stage the offline keypad virtual pet (org.kyf37.tama) into the tree as packages/apps/Kyf37Tama.
import pathlib, shutil
WS = pathlib.Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/kyf37-tama')
app = pathlib.Path.home() / 'kyf37-android10/packages/apps/Kyf37Tama'
if (app / 'src').exists(): shutil.rmtree(app / 'src')
shutil.copytree(WS / 'src', app / 'src')
(app / 'res/drawable-nodpi').mkdir(parents=True, exist_ok=True)
shutil.copy2(WS / 'res/drawable-nodpi/ic_tama.png', app / 'res/drawable-nodpi/ic_tama.png')
(app / 'Android.mk').write_text('LOCAL_PATH := $(call my-dir)\ninclude $(CLEAR_VARS)\nLOCAL_MODULE_TAGS := optional\nLOCAL_PACKAGE_NAME := Kyf37Tama\n'
    'LOCAL_SRC_FILES := $(call all-java-files-under, src)\nLOCAL_CERTIFICATE := platform\nLOCAL_SDK_VERSION := current\ninclude $(BUILD_PACKAGE)\n', newline=chr(10))
(app / 'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.tama" android:versionCode="1" android:versionName="1.0">
 <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="29" />
 <application android:label="Pet" android:icon="@drawable/ic_tama" android:allowBackup="false" android:theme="@android:style/Theme.Material.NoActionBar">
  <activity android:name=".Tama" android:exported="true" android:screenOrientation="portrait" android:configChanges="keyboardHidden|orientation|screenSize">
   <intent-filter><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent-filter>
  </activity>
 </application>
</manifest>
''', newline=chr(10))
mk = pathlib.Path.home() / 'kyf37-android10/device/kyocera/kyf37/device.mk'
t = mk.read_text()
if 'Kyf37Tama' not in t:
    mk.write_text(t.rstrip(chr(10)) + chr(10) + 'PRODUCT_PACKAGES += Kyf37Tama' + chr(10), newline=chr(10)); print('device.mk: Kyf37Tama')
print('Kyf37Tama staged')
