from pathlib import Path
import subprocess,shutil
root=Path('/home/pablo/kyf37-android10')
src=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/tools/tt9/tt9-v64.0-full.apk')
p=root/'packages/apps/TraditionalT9'
p.mkdir(exist_ok=True)
shutil.copy2(src,p/'TraditionalT9.apk')
(p/'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := TraditionalT9
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := TraditionalT9.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)
''')
p=root/'device/kyocera/kyf37/device.mk'
s=p.read_text()
if 'PRODUCT_PACKAGES += TraditionalT9' not in s:s+='\nPRODUCT_PACKAGES += TraditionalT9\n'
p.write_text(s)
print('TT9 full v64.0 added as upstream-signed system app; rerun build after current build completes')
