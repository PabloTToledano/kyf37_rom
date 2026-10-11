"""KYF37 owner item 5: every preinstalled app gets all runtime permissions by default. Idempotent; WSL Python 3.

Framework: DefaultPermissionGrantPolicy.grantPermissionsToSysComponentsAndPrivApps() granted only for sys components /
persistent platform-signed priv apps. It now also grants every runtime permission requested by EVERY FLAG_SYSTEM package
(not systemFixed for the new ones, so the user can still revoke in Settings). Runs from PackageManagerService on first
boot, on a build fingerprint change (flashing a new ROM) and for new users, i.e. also after a data reset.
Fallback: etc/default-permissions/default-permissions-kyf37-all.xml (explicit list measured on the v18 phone as still
ungranted; fixed=false). Applied live on v18 with `pm grant` (see kyf37-rom/keypad-nav-v18/perms-*.txt).
"""
from pathlib import Path
WS = Path(__file__).resolve().parent.parent
ROOT = Path('/home/pablo/kyf37-android10')
pol = ROOT / 'frameworks/base/services/core/java/com/android/server/pm/permission/DefaultPermissionGrantPolicy.java'
s = pol.read_text()
if 'Kyf37: all system apps' not in s:
    old = """            if (!isSysComponentOrPersistentPlatformSignedPrivApp(pkg)
                    || !doesPackageSupportRuntimePermissions(pkg)
                    || ArrayUtils.isEmpty(pkg.requestedPermissions)) {
                continue;
            }
            grantRuntimePermissionsForSystemPackage(userId, pkg);"""
    new = """            // Kyf37: all system apps get their runtime permissions by default (revocable by the user).
            final boolean platform = isSysComponentOrPersistentPlatformSignedPrivApp(pkg);
            if (pkg.applicationInfo == null || !pkg.applicationInfo.isSystemApp()
                    || !doesPackageSupportRuntimePermissions(pkg)
                    || ArrayUtils.isEmpty(pkg.requestedPermissions)) {
                continue;
            }
            grantRuntimePermissionsForSystemPackage(userId, pkg, platform);"""
    assert old in s
    s = s.replace(old, new)
    old2 = "    private void grantRuntimePermissionsForSystemPackage(int userId, PackageInfo pkg) {"
    assert old2 in s
    s = s.replace(old2, "    private void grantRuntimePermissionsForSystemPackage(int userId, PackageInfo pkg,\n            boolean systemFixed) {")
    old3 = "            grantRuntimePermissions(pkg, permissions, true /*systemFixed*/, userId);\n        }\n    }\n\n    public void scheduleRead"
    assert old3 in s
    s = s.replace(old3, "            grantRuntimePermissions(pkg, permissions, systemFixed, userId);\n        }\n    }\n\n    public void scheduleRead")
    pol.write_text(s)
    print('patched DefaultPermissionGrantPolicy')

lst = WS / 'kyf37-rom/keypad-nav-v18/perms-ungranted-before.txt'
by = {}
for line in lst.read_text().split('\n'):
    line = line.strip()
    if line:
        pk, pm = line.split()
        by.setdefault(pk, []).append(pm)
extra = {
    'com.android.dialer': ['CALL_PHONE', 'READ_PHONE_STATE', 'READ_CONTACTS', 'WRITE_CONTACTS', 'READ_CALL_LOG',
                           'WRITE_CALL_LOG', 'RECORD_AUDIO', 'READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE'],
    'com.android.messaging': ['READ_SMS', 'SEND_SMS', 'RECEIVE_SMS', 'RECEIVE_MMS', 'READ_CONTACTS',
                              'READ_PHONE_STATE', 'READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE'],
    'com.android.camera2': ['CAMERA', 'RECORD_AUDIO', 'ACCESS_FINE_LOCATION', 'READ_EXTERNAL_STORAGE',
                            'WRITE_EXTERNAL_STORAGE'],
}
for k, v in extra.items():
    lst2 = by.setdefault(k, [])
    for p in v:
        p = 'android.permission.' + p
        if p not in lst2:
            lst2.append(p)
xml = '<?xml version="1.0" encoding="utf-8"?>\n<exceptions>\n'
for k in sorted(by):
    xml += '    <exception package="%s">\n' % k
    for p in by[k]:
        xml += '        <permission name="%s" fixed="false" />\n' % p
    xml += '    </exception>\n'
xml += '</exceptions>\n'
dev = ROOT / 'device/kyocera/kyf37'
(dev / 'permissions/default-permissions-kyf37-all.xml').write_text(xml)
mk = dev / 'device.mk'
m = mk.read_text()
line = ('PRODUCT_COPY_FILES += device/kyocera/kyf37/permissions/default-permissions-kyf37-all.xml:'
        '$(TARGET_COPY_OUT_SYSTEM)/etc/default-permissions/default-permissions-kyf37-all.xml')
if line not in m:
    mk.write_text(m.rstrip() + '\n' + line + '\n')
    print('device.mk copy rule')
