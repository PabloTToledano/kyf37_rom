"""Reproducible offline app/helper staging. Optional --include-rom adds product rule."""
from pathlib import Path
import shutil,sys
ws=Path(__file__).resolve().parent
root=Path.home()/'kyf37-android10';app=root/'packages/apps/Kyf37Remote'
src=app/'src/org/kyf37/remote';src.mkdir(parents=True,exist_ok=True)
for n in ('Remote.java','IrSignals.java'):shutil.copy2(ws/'ir-remote'/n,src/n)
native=app/'native';native.mkdir(exist_ok=True)
for n in ('kyf37_ir_tx.c','kyf37_ir_service.c','kyf37_ir_uapi.h'):shutil.copy2(ws/'ir-remote'/n,native/n)
(app/'Android.bp').write_text('''cc_binary {
 name: "kyf37_ir_tx", srcs: ["native/kyf37_ir_tx.c"],
 compile_multilib: "32", cflags: ["-Wall", "-Wextra", "-Werror"],
}
cc_binary {
 name: "kyf37_ir_service", srcs: ["native/kyf37_ir_service.c"],
 compile_multilib: "32", cflags: ["-Wall", "-Wextra", "-Werror"],
}
''')
(app/'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_PACKAGE_NAME := Kyf37Remote
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_SDK_VERSION := current
LOCAL_CERTIFICATE := platform
include $(BUILD_PACKAGE)
''')
(app/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.remote" android:sharedUserId="android.uid.system" android:versionCode="2" android:versionName="0.2-experimental">
 <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="28"/>
 <uses-permission android:name="android.permission.TRANSMIT_IR"/>
 <uses-feature android:name="android.hardware.consumerir" android:required="false"/>
 <uses-feature android:name="android.hardware.touchscreen" android:required="false"/>
 <uses-feature android:name="android.hardware.faketouch" android:required="false"/>
 <application android:label="IR Remote" android:theme="@android:style/Theme.Material.NoActionBar" android:allowBackup="false" android:icon="@android:drawable/ic_menu_manage">
  <activity android:name=".Remote" android:exported="true" android:screenOrientation="portrait">
   <intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
  </activity>
 </application>
</manifest>
''')
assets=app/'assets';assets.mkdir(exist_ok=True)
helper=root/'out/target/product/kyf37/system/bin/kyf37_ir_tx'
if '--embed-helper' in sys.argv:
    assert helper.exists(),'Build kyf37_ir_tx first'
    shutil.copy2(helper,assets/'kyf37_ir_tx')
if '--include-rom' in sys.argv:
    p=root/'device/kyocera/kyf37/device.mk';s=p.read_text()
    if 'PRODUCT_PACKAGES += Kyf37Remote kyf37_ir_tx' not in s:p.write_text(s+'\nPRODUCT_PACKAGES += Kyf37Remote kyf37_ir_tx\n')
print('Keypad IR app/helper staged offline; no product change unless --include-rom, no phone access')
