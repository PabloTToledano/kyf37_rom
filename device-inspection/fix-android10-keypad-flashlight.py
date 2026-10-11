"""Replace MobileLight in future ROMs with a keypad-controlled torch app."""
from pathlib import Path
import json, re, shutil, sys
WS=Path(__file__).resolve().parent.parent
ROOT=Path('/home/pablo/kyf37-android10')
app=ROOT/'packages/apps/Kyf37Flashlight'
src=app/'src/org/kyf37/flashlight';src.mkdir(parents=True,exist_ok=True)
shutil.copy2(WS/'device-inspection/Kyf37Flashlight.java.txt',src/'Flashlight.java')
if '--source-only' in sys.argv:
    print('Flashlight activity updated');sys.exit(0)
(app/'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE_TAGS := optional
LOCAL_PACKAGE_NAME := Kyf37Flashlight
LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_CERTIFICATE := platform
LOCAL_SDK_VERSION := current
LOCAL_OVERRIDES_PACKAGES := MobileLight
include $(BUILD_PACKAGE)
''')
(app/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.flashlight" android:versionCode="1" android:versionName="1.0">
 <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="29" />
 <uses-permission android:name="android.permission.CAMERA" />
 <uses-feature android:name="android.hardware.camera.flash" android:required="false" />
 <application android:label="Flashlight" android:icon="@drawable/sky_flashlight" android:allowBackup="false" android:theme="@android:style/Theme.Material.NoActionBar">
  <activity android:name=".Flashlight" android:exported="true" android:screenOrientation="portrait">
   <intent-filter><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent-filter>
  </activity>
 </application>
</manifest>
''')
draw=app/'res/drawable-nodpi';draw.mkdir(parents=True,exist_ok=True)
shutil.copy2(WS/'kyf37-rom/sky-star-icons/icons/sky_flashlight.png',draw/'sky_flashlight.png')
shutil.copy2(WS/'kyf37-rom/pastel-star-icons/icons/pastel_flashlight.png',draw/'pastel_flashlight.png')
dm=ROOT/'device/kyocera/kyf37/device.mk';s=dm.read_text()
s=re.sub(r'(?<= )MobileLight(?=\s)','Kyf37Flashlight',s)
if 'PRODUCT_PACKAGES += Kyf37Flashlight' not in s and 'Kyf37Flashlight' not in s:s+='\nPRODUCT_PACKAGES += Kyf37Flashlight\n'
dm.write_text(s)
# Camera permission is granted for the bundled foreground torch app on new ROMs.
per=ROOT/'device/kyocera/kyf37/permissions/default-permissions-kyf37-flashlight.xml'
per.write_text('''<exceptions><exception package="org.kyf37.flashlight">
 <permission name="android.permission.CAMERA" fixed="false" />
</exception></exceptions>
''')
s=dm.read_text()
if 'default-permissions-kyf37-flashlight.xml' not in s:s+='\nPRODUCT_COPY_FILES += device/kyocera/kyf37/permissions/default-permissions-kyf37-flashlight.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/default-permissions/default-permissions-kyf37-flashlight.xml\n'
dm.write_text(s)
p=WS/'device-inspection/fix-android10-pastel-icons.py'
s=p.read_text().replace("'flashlight': 'jp.kyocera.mobilelight'","'flashlight': 'jp.kyocera.mobilelight org.kyf37.flashlight'")
p.write_text(s)
for pack in ('pastel-star','sky-star'):
    assets=ROOT/'packages/apps/Kyf37Home/assets'/pack
    p=assets/'packages.properties';s=p.read_text()
    if 'org.kyf37.flashlight=' not in s:s+='org.kyf37.flashlight=flashlight\n'
    p.write_text(s)
    folder=WS/'kyf37-rom'/(pack+'-icons')
    p=folder/'packages.properties';s=p.read_text()
    if 'org.kyf37.flashlight=' not in s:s+='org.kyf37.flashlight=flashlight\n'
    p.write_text(s)
    p=folder/'packages.json';data=json.loads(p.read_text());data['org.kyf37.flashlight']='flashlight';p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
print('Kyf37Flashlight staged, MobileLight excluded from future ROMs, both Home icon themes mapped')
