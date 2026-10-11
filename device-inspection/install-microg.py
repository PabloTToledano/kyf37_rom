"""Integrate microG (GmsCore, companion store stub, GSF proxy) + signature spoofing into the ROM source. WSL; idempotent.

Sources (verified SHA-256 against the repo index, https://microg.org/fdroid/repo):
  com.google.android.gms-252432034.apk  (GmsCore 0.3.17.252432)
  com.android.vending-84022634.apk      (microG Companion / FakeStore 0.3.17.40226)
  com.google.android.gsf-8.apk          (GSF proxy v0.1.0)
Framework patch: lineageos4microg/docker-lineage-cicd android_frameworks_base-Q.patch (FAKE_PACKAGE_SIGNATURE + fused provider).
"""
import re, shutil, subprocess, zipfile
from pathlib import Path

root = Path('/home/pablo/kyf37-android10')
dl = Path('/home/pablo/microg')
dev = root / 'device/kyocera/kyf37'
pkgdir = root / 'packages/apps/MicroG'
APKS = [('GmsCore', 'com.google.android.gms', 'com.google.android.gms-252432034.apk'),
        ('FakeStore', 'com.android.vending', 'com.android.vending-84022634.apk'),
        ('GsfProxy', 'com.google.android.gsf', 'com.google.android.gsf-8.apk')]

# 1. Signature spoofing patch (idempotent)
fw = root / 'frameworks/base'
marker = fw / 'core/res/AndroidManifest.xml'
if 'FAKE_PACKAGE_SIGNATURE' not in marker.read_text():
    r = subprocess.run(['patch', '-p1', '-i', str(dl / 'q.patch')], cwd=fw, capture_output=True, text=True)
    print(r.stdout[-600:], r.stderr[-600:])
    assert r.returncode == 0, 'signature spoofing patch failed'
else:
    print('signature spoofing already applied')

# 2. Package the APKs as prebuilt privileged apps
pkgdir.mkdir(parents=True, exist_ok=True)
mk = ['LOCAL_PATH := $(call my-dir)\n']
def strip_abis(src, dst):
    """Keep only armeabi-v7a native code (this phone is ARM32) and drop the old signature; the build re-signs it."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            n = info.filename
            if n.startswith('META-INF/'): continue
            if n.startswith('lib/') and not n.startswith('lib/armeabi-v7a/'): continue
            zout.writestr(info, zin.read(n), compress_type=info.compress_type)

for name, pkg, apk in APKS:
    shutil.copy2(dl / apk, pkgdir / (name + '.apk'))
    mk.append(f'''include $(CLEAR_VARS)
LOCAL_MODULE := {name}
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := {name}.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SIGNATURE_SUFFIX_PLACEHOLDER)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_PRIVILEGED_MODULE := true
LOCAL_DEX_PREOPT := false
LOCAL_MODULE_PATH := $(TARGET_OUT)/priv-app
include $(BUILD_PREBUILT)
''')
mk = '\n'.join(mk).replace('$(COMMON_ANDROID_PACKAGE_SIGNATURE_SUFFIX_PLACEHOLDER)', '$(COMMON_ANDROID_PACKAGE_SUFFIX)')
(pkgdir / 'Android.mk').write_text(mk)

# 3. privapp allowlists: every signature|privileged permission each app requests
priv_levels = {}
def scan_manifest(p):
    try: t = p.read_text(errors='ignore')
    except Exception: return
    for m in re.finditer(r'<permission\b[^>]*?android:name="([^"]+)"[^>]*?>', t, re.S):
        tag = m.group(0)
        lvl = re.search(r'android:protectionLevel="([^"]+)"', tag)
        if lvl and 'privileged' in lvl.group(1): priv_levels[m.group(1)] = lvl.group(1)
for base in [root / 'frameworks/base/core/res', root / 'lineage-sdk', root / 'packages/apps', root / 'packages/services', root / 'frameworks/opt']:
    for p in base.rglob('AndroidManifest.xml'):
        if '/out/' in str(p): continue
        scan_manifest(p)
aapt2 = root / 'out/host/linux-x86/bin/aapt2'
xml = ['<?xml version="1.0" encoding="utf-8"?>\n<permissions>']
report = {}
for name, pkg, apk in APKS:
    out = subprocess.run([str(aapt2), 'dump', 'permissions', str(dl / apk)], capture_output=True, text=True).stdout
    asked = re.findall(r"uses-permission(?:-sdk-23)?: name='([^']+)'", out)
    need = sorted(p for p in set(asked) if p in priv_levels)
    report[pkg] = need
    xml.append(f'    <privapp-permissions package="{pkg}">')
    xml += [f'        <permission name="{p}"/>' for p in need]
    xml.append('    </privapp-permissions>')
xml.append('</permissions>\n')
(dev / 'permissions').mkdir(exist_ok=True)
(dev / 'permissions/privapp-permissions-microg.xml').write_text('\n'.join(xml))

# 4. Runtime permissions granted by default (FAKE_PACKAGE_SIGNATURE is dangerous in the patch, so it must be pre-granted)
(dev / 'permissions/default-permissions-microg.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<exceptions>
    <exception package="com.google.android.gms">
        <permission name="android.permission.FAKE_PACKAGE_SIGNATURE" fixed="false"/>
        <permission name="android.permission.ACCESS_FINE_LOCATION" fixed="false"/>
        <permission name="android.permission.ACCESS_COARSE_LOCATION" fixed="false"/>
        <permission name="android.permission.ACCESS_BACKGROUND_LOCATION" fixed="false"/>
        <permission name="android.permission.READ_PHONE_STATE" fixed="false"/>
        <permission name="android.permission.GET_ACCOUNTS" fixed="false"/>
        <permission name="android.permission.READ_EXTERNAL_STORAGE" fixed="false"/>
        <permission name="android.permission.WRITE_EXTERNAL_STORAGE" fixed="false"/>
    </exception>
    <exception package="com.android.vending">
        <permission name="android.permission.FAKE_PACKAGE_SIGNATURE" fixed="false"/>
    </exception>
</exceptions>
''')

# 5. device.mk wiring
p = dev / 'device.mk'; s = p.read_text()
add = '''
# microG (open Google Play Services replacement) + signature spoofing; see MICROG.md
PRODUCT_PACKAGES += GmsCore FakeStore GsfProxy
PRODUCT_COPY_FILES += device/kyocera/kyf37/permissions/privapp-permissions-microg.xml:system/etc/permissions/privapp-permissions-microg.xml \\
    device/kyocera/kyf37/permissions/default-permissions-microg.xml:system/etc/default-permissions/default-permissions-microg.xml
'''
if 'privapp-permissions-microg.xml' not in s: p.write_text(s.rstrip() + '\n' + add)
print('privileged permissions allowlisted:', {k: len(v) for k, v in report.items()})
print('permissions defined as privileged in tree:', len(priv_levels))
