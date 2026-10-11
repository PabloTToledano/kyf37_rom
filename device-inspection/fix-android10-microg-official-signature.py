#!/usr/bin/env python3
"""Keep official microG APK signatures for restricted spoofing and Companion IPC.

Run under the build wrapper lock. Do not strip signed APK entries: doing so
forced GmsCore onto the ROM testkey, breaking its signature permissions and
PackageManagerService.isMicrogSigned (including modern SigningInfo spoofing).
"""
from pathlib import Path
import hashlib
import shutil

root = Path('/home/pablo/kyf37-android10')
src = Path('/home/pablo/microg/com.google.android.gms-252432034.apk')
dst = root / 'packages/apps/MicroG/GmsCore.apk'
mk = dst.parent / 'Android.mk'
text = mk.read_text()
start = text.index('LOCAL_MODULE := GmsCore\n')
end = text.index('include $(BUILD_PREBUILT)', start)
block = text[start:end]
assert 'LOCAL_CERTIFICATE := testkey' in block or 'LOCAL_CERTIFICATE := PRESIGNED' in block
updated = text[:start] + block.replace('LOCAL_CERTIFICATE := testkey', 'LOCAL_CERTIFICATE := PRESIGNED') + text[end:]
if updated != text:
    mk.write_text(updated)
digest = lambda p: hashlib.sha256(p.read_bytes()).digest()
if not dst.exists() or digest(src) != digest(dst):
    shutil.copyfile(src, dst)
assert digest(src) == digest(dst)

# Ensure Kati/Ninja rebuilds GmsCore and does not retain stale testkey-signed artifacts
out_apk = root / 'out/target/product/kyf37/system/priv-app/GmsCore/GmsCore.apk'
out_inter = root / 'out/target/product/kyf37/obj/APPS/GmsCore_intermediates'
if out_apk.exists() and digest(out_apk) != digest(src):
    print('Removing stale build output GmsCore.apk')
    out_apk.unlink()
if out_inter.exists():
    inter_apk = out_inter / 'package.apk'
    if not inter_apk.exists() or digest(inter_apk) != digest(src):
        print('Removing stale GmsCore intermediates')
        shutil.rmtree(out_inter, ignore_errors=True)

# Pre-grant battery optimization exemption via sysconfig
sysconfig_dir = root / 'device/kyocera/kyf37/permissions'
sysconfig_xml = sysconfig_dir / 'sysconfig-microg.xml'
sysconfig_content = '''<?xml version="1.0" encoding="utf-8"?>
<config>
    <allow-in-power-save package="com.google.android.gms" />
    <allow-in-power-save-except-idle package="com.google.android.gms" />
</config>
'''
if not sysconfig_xml.exists() or sysconfig_xml.read_text() != sysconfig_content:
    sysconfig_xml.write_text(sysconfig_content)

dev_mk = root / 'device/kyocera/kyf37/device.mk'
dev_text = dev_mk.read_text()
copy_entry = 'device/kyocera/kyf37/permissions/sysconfig-microg.xml:system/etc/sysconfig/sysconfig-microg.xml'
if copy_entry not in dev_text:
    target_pattern = 'device/kyocera/kyf37/permissions/default-permissions-microg.xml:system/etc/default-permissions/default-permissions-microg.xml'
    if target_pattern in dev_text:
        dev_mk.write_text(dev_text.replace(target_pattern, target_pattern + ' \\\n    ' + copy_entry))
        print('Added sysconfig-microg.xml to device.mk PRODUCT_COPY_FILES')

print('GmsCore restored byte-for-byte; official APK signature preserved')


