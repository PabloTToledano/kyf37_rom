"""Stage the new keypad front end; retain the original Data Folder APK as the port base."""
from pathlib import Path
here=Path(__file__).resolve().parent
tree=Path('/home/pablo/kyf37-android10')
dest=tree/'packages/apps/Kyf37GalleryCode'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists() or p.read_text()!=s:p.write_text(s,encoding='utf-8',newline='\n')
for p in (here/'kyf37-gallery').glob('*.java'):
    if p.name.endswith('Test.java') or p.name=='GalleryInstrumentation.java':continue
    write(dest/'src/org/kyf37/gallery'/p.name,p.read_text(encoding='utf-8'))
tests=tree/'packages/apps/Kyf37GalleryTests'
for p in (here/'kyf37-gallery').glob('*.java'):
    if p.name.endswith('Test.java'):continue
    write(tests/'src/org/kyf37/gallery'/p.name,p.read_text(encoding='utf-8'))
for p in (here/'kyf37-gallery/test-assets').glob('*'):
    target=tests/'assets'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() or target.read_bytes()!=p.read_bytes():target.write_bytes(p.read_bytes())
write(tests/'Android.mk','''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE_TAGS := tests
LOCAL_PACKAGE_NAME := Kyf37GalleryTests
LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_CERTIFICATE := platform
LOCAL_SDK_VERSION := current
LOCAL_DEX_PREOPT := false
LOCAL_PROGUARD_ENABLED := disabled
include $(BUILD_PACKAGE)
''')
write(tests/'AndroidManifest.xml','''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.gallery.tests">
<uses-sdk android:minSdkVersion="29" android:targetSdkVersion="29"/>
<application android:label="Synthetic Gallery tests"/>
<instrumentation android:name="org.kyf37.gallery.GalleryInstrumentation" android:targetPackage="jp.kyocera.datafolder"/>
</manifest>''')
write(dest/'Android.mk','''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE_TAGS := optional
LOCAL_PACKAGE_NAME := Kyf37GalleryCode
LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_CERTIFICATE := platform
LOCAL_SDK_VERSION := current
LOCAL_DEX_PREOPT := false
LOCAL_PROGUARD_ENABLED := disabled
include $(BUILD_PACKAGE)
''')
write(dest/'AndroidManifest.xml','''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.gallery.code">
<uses-sdk android:minSdkVersion="29" android:targetSdkVersion="29"/>
<application android:label="Gallery code payload" android:hasCode="true"/>
</manifest>''')
p=tree/'device/kyocera/kyf37/device.mk';s=p.read_text()
if '# KYF37 modern Kyocera gallery' not in s:s+='\n# KYF37 modern Kyocera gallery: original APK with a keypad front end.\nPRODUCT_PACKAGES += Kyf37StockDataFolder\n'
write(p,s)
# Prefer this gallery tile while retaining Gallery2 as an available native fallback.
p=here/'Kyf37HomeRedesign.java.txt';s=p.read_text(encoding='utf-8')
anchor='        hideLegacy(pm, seen, "org.kyf37.contacts", "com.android.contacts");'
line='        hideLegacy(pm, seen, "jp.kyocera.datafolder", "com.android.gallery3d");'
if line not in s:
    assert anchor in s;s=s.replace(anchor,anchor+'\n'+line)
write(p,s)
print('Kyocera gallery source and ROM module staged')
