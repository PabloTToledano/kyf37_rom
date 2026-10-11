#!/usr/bin/env python3
"""Idempotent: stage Magisk v23 (runtime-daemon mode) into the KYF37 vendor tree.
Ships /system/xbin/magisk (+su symlink via PRODUCT_COPY_FILES-free post-install rule), Magisk app,
init service starting magiskd at sys.boot_completed. Opt out: setprop persist.kyf37.magisk 0.
Run: wsl -d Ubuntu -- python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-magisk.py"""
import shutil, zipfile, pathlib
here = pathlib.Path(__file__).resolve().parent
ven = pathlib.Path.home() / 'kyf37-android10/vendor/kyocera/kyf37'
dev = pathlib.Path.home() / 'kyf37-android10/device/kyocera/kyf37'
d = ven / 'proprietary/magisk'; d.mkdir(parents=True, exist_ok=True)
apk = here / 'Magisk-v23.0.apk'
with zipfile.ZipFile(apk) as z:
    (d / 'magisk').write_bytes(z.read('lib/armeabi-v7a/libmagisk32.so'))
shutil.copyfile(apk, d / 'Magisk.apk')
shutil.copyfile(here / 'kyf37-magisk.sh', d / 'kyf37-magisk.sh')
shutil.copyfile(here / 'init.kyf37.magisk.rc', d / 'init.kyf37.magisk.rc')
P = 'vendor/kyocera/kyf37/proprietary/magisk/'
lines = [P + 'magisk:system/xbin/magisk',
         P + 'kyf37-magisk.sh:system/etc/kyf37-magisk.sh',
         P + 'init.kyf37.magisk.rc:system/etc/init/init.kyf37.magisk.rc']
mk = ven / 'kyf37-vendor.mk'
t = mk.read_text()
add = [l for l in lines if l not in t]
if add:
    mk.write_text(t.rstrip('\n') + '\n' + ''.join('PRODUCT_COPY_FILES += %s\n' % l for l in add)); print('copy rules added:', len(add))
app = pathlib.Path.home() / 'kyf37-android10/packages/apps/MagiskApp'; app.mkdir(parents=True, exist_ok=True)
shutil.copyfile(apk, app / 'Magisk.apk')
(app / 'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := Magisk
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := Magisk.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)
''')
dm0 = dev / 'device.mk'
NL = chr(10)
if 'PRODUCT_PACKAGES += Magisk' + NL not in dm0.read_text() + NL:
    dm0.write_text(dm0.read_text().rstrip(NL) + NL + 'PRODUCT_PACKAGES += Magisk' + NL)
dm = dev / 'device.mk'
NL = chr(10)
t2 = dm.read_text().replace('-include device/kyocera/kyf37/magisk-su.mk' + NL, '')
dm.write_text(t2)
print('magisk staged')
