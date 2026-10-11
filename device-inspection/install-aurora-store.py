"""Preinstall Aurora Store (owner-supplied APK) into the ROM. WSL; idempotent.
APK: ~/microg/AuroraStore.apk  (com.aurora.store 4.8.4, sha256 8a1ed9aa…a4bad), original signature kept (PRESIGNED) so the app can self-update.
Installed as an ordinary system app (not privileged)."""
import shutil
from pathlib import Path
root = Path('/home/pablo/kyf37-android10')
d = root / 'packages/apps/AuroraStore'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2('/home/pablo/microg/AuroraStore.apk', d / 'AuroraStore.apk')
(d / 'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := AuroraStore
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := AuroraStore.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)
''')
p = root / 'device/kyocera/kyf37/device.mk'; s = p.read_text()
if 'AuroraStore' not in s: p.write_text(s.rstrip() + '\nPRODUCT_PACKAGES += AuroraStore\n')
print('AuroraStore wired')
