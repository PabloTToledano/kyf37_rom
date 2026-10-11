"""KYF37 keitai Phone / Messages / Contacts apps (KEITAI-APPS.md). Idempotent; WSL Python 3.

Stages three plain-framework apps built from device-inspection/keitai-apps/{dialer,messages,contacts} into the tree:
  packages/apps/Kyf37Dialer   org.kyf37.dialer    default dialer + in-call UI + call log + speed dial
  packages/apps/Kyf37Messages org.kyf37.messages  default SMS app (SMS full, MMS basics)
  packages/apps/Kyf37Contacts org.kyf37.contacts  contacts list/view/edit, vCard import/export, PICK/VIEW/INSERT_OR_EDIT
and wires them in:
  * device.mk PRODUCT_PACKAGES (the stock Lineage Dialer / Messaging / Contacts stay installed, just not default)
  * framework-res overlay: config_defaultDialer, config_defaultSms, default_sms_application
  * Telecomm / Telephony overlay: dialer_default_class, ui_default_package (used for MMI codes and "return to call")
  * intent filters carry priority 100, so the keitai apps win ACTION_DIAL / SENDTO / VIEW contacts over the Lineage apps
  * Kyf37Home: hides the Lineage Dialer/Messaging/Contacts launcher tiles when ours are present; icon map entries
  * build-kyf37-android10.sh: this script is chained into the UI-script loop
Apps are platform-signed, NOT priv-apps, so no privapp-permissions allowlist is needed (see AGENTS.md section 4).
Runtime permissions are granted by fix-android10-default-permissions.py (every FLAG_SYSTEM package).
"""
import os
import re
import shutil
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
ROOT = Path('/home/pablo/kyf37-android10')
SRC = WS / 'device-inspection' / 'keitai-apps'
FOCUS = WS / 'device-inspection' / 'Kyf37FocusCompat.java.txt'
HOME_ASSETS = ROOT / 'packages/apps/Kyf37Home/assets/pastel-star'

APPS = {
    'dialer':   dict(module='Kyf37Dialer',   pkg='org.kyf37.dialer',   icon='pastel_phone.png',    role=True),
    'messages': dict(module='Kyf37Messages', pkg='org.kyf37.messages', icon='pastel_messages.png', role=True),
    'contacts': dict(module='Kyf37Contacts', pkg='org.kyf37.contacts', icon='pastel_contacts.png', role=False),
}


def write_if_changed(path, text, binary=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        if path.exists() and path.read_bytes() == text:
            return False
        path.write_bytes(text)
        return True
    text = text.replace('\r\n', '\n')
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
    path.write_text(text, encoding='utf-8', newline='\n')
    return True


def stage_app(name, info):
    app = ROOT / 'packages/apps' / info['module']
    pkgdir = app / 'src/org/kyf37' / name
    changed = False
    wanted = set()
    for f in sorted((SRC / name).glob('*.java')):
        wanted.add(f.name)
        changed |= write_if_changed(pkgdir / f.name, f.read_text(encoding='utf-8'))
    for f in sorted((SRC / 'common').glob('*.java')):
        wanted.add(f.name)
        changed |= write_if_changed(pkgdir / f.name, f.read_text(encoding='utf-8').replace('@PKG@', info['pkg']))
    wanted.add('Kyf37FocusCompat.java')
    changed |= write_if_changed(pkgdir / 'Kyf37FocusCompat.java', FOCUS.read_text(encoding='utf-8').replace('@PKG@', info['pkg']))
    if info['role']:
        wanted.add('RoleBoot.java')
        changed |= write_if_changed(pkgdir / 'RoleBoot.java', (SRC / 'role/RoleBoot.java').read_text(encoding='utf-8').replace('@PKG@', info['pkg']))
    if pkgdir.exists():
        for old in pkgdir.glob('*.java'):
            if old.name not in wanted:
                old.unlink()
                changed = True
    changed |= write_if_changed(app / 'AndroidManifest.xml', (SRC / name / 'AndroidManifest.xml').read_text(encoding='utf-8'))
    icon = HOME_ASSETS / info['icon']
    if icon.exists():
        changed |= write_if_changed(app / 'res/drawable-nodpi/ic_launcher.png', icon.read_bytes(), binary=True)
    else:
        print('WARN launcher icon source missing', icon)
    mk = (
        'LOCAL_PATH := $(call my-dir)\n'
        'include $(CLEAR_VARS)\n'
        'LOCAL_MODULE_TAGS := optional\n'
        'LOCAL_PACKAGE_NAME := %s\n'
        'LOCAL_SRC_FILES := $(call all-java-files-under, src)\n'
        'LOCAL_CERTIFICATE := platform\n'
        'LOCAL_SDK_VERSION := system_current\n'
        'include $(BUILD_PACKAGE)\n' % info['module'])
    changed |= write_if_changed(app / 'Android.mk', mk)
    print('app %-13s %s' % (info['module'], 'updated' if changed else 'unchanged'))


for n, i in APPS.items():
    stage_app(n, i)

# ------------------------------------------------------------------------------------------------ product packages
dm = ROOT / 'device/kyocera/kyf37/device.mk'
s = dm.read_text()
add = [i['module'] for i in APPS.values() if i['module'] not in s]
if add:
    dm.write_text(s.rstrip() + '\n# keitai Phone / Messages / Contacts (fix-android10-keitai-apps.py)\nPRODUCT_PACKAGES += ' + ' '.join(add) + '\n')
    print('device.mk: +', ' '.join(add))

# ------------------------------------------------------------------------------------------------ overlays
OV = ROOT / 'device/kyocera/kyf37/overlay'
write_if_changed(OV / 'frameworks/base/core/res/res/values/kyf37_keitai_apps.xml', '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Role defaults: applied by RoleManager when the role has no holder (clean install). RoleBoot in each app handles updates. -->
    <string name="config_defaultDialer" translatable="false">org.kyf37.dialer</string>
    <string name="default_sms_application" translatable="false">org.kyf37.messages</string>
    <string name="config_defaultSms" translatable="false">org.kyf37.messages</string>
</resources>
''')
write_if_changed(OV / 'packages/services/Telecomm/res/values/kyf37_dialer.xml', '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="dialer_default_class" translatable="false">org.kyf37.dialer.DialerActivity</string>
</resources>
''')
write_if_changed(OV / 'packages/services/Telephony/res/values/kyf37_dialer.xml', '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="ui_default_package" translatable="false">org.kyf37.dialer</string>
    <string name="dialer_default_class" translatable="false">org.kyf37.dialer.DialerActivity</string>
</resources>
''')

# ------------------------------------------------------------------------------------------------ Home: icons + hide legacy tiles
props = ROOT / 'packages/apps/Kyf37Home/assets/pastel-star/packages.properties'
if props.exists():
    t = props.read_text()
    extra = {'org.kyf37.dialer': 'phone', 'org.kyf37.messages': 'messages', 'org.kyf37.contacts': 'contacts'}
    missing = [k + '=' + v for k, v in extra.items() if (k + '=') not in t]
    if missing:
        props.write_text(t.rstrip('\n') + '\n' + '\n'.join(missing) + '\n')
        print('icon map: +', missing)

HIDE_MARK = 'Kyf37 keitai apps: hide the stock Lineage tiles'
HIDE = '''        // Kyf37 keitai apps: hide the stock Lineage tiles when the keitai replacements are installed.
        hideLegacy(pm, seen, "org.kyf37.dialer", "com.android.dialer");
        hideLegacy(pm, seen, "org.kyf37.messages", "com.android.messaging");
        hideLegacy(pm, seen, "org.kyf37.contacts", "com.android.contacts");
'''
HIDE_METHOD = '''    private void hideLegacy(PackageManager pm, HashSet<String> seen, String keitai, String legacy) {
        try {
            pm.getPackageInfo(keitai, 0);
            seen.add(legacy);
        } catch (PackageManager.NameNotFoundException e) {
            // keitai app absent: leave the stock one visible
        }
    }

'''
for home in [ROOT / 'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java', WS / 'device-inspection/Kyf37Home.java.txt']:
    if not home.exists():
        continue
    h = home.read_text()
    if HIDE_MARK in h:
        continue
    anchor = '        Intent query = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);'
    if anchor not in h:
        print('WARN Home anchor missing in', home)
        continue
    h = h.replace(anchor, HIDE + anchor, 1)
    m_anchor = '    private void addFixed('
    h = h.replace(m_anchor, HIDE_METHOD + m_anchor, 1)
    home.write_text(h)
    print('Home patched:', home)

# ------------------------------------------------------------------------------------------------ chain into the build script
bs = WS / 'device-inspection/build-kyf37-android10.sh'
b = bs.read_text()
if 'keitai-apps' not in b:
    nb, n = re.subn(r'(for kyf37_nav in [^;]*?)(; do)', lambda m: m.group(1) + ' keitai-apps' + m.group(2), b, count=1)
    if n:
        tmp = bs.with_suffix('.sh.tmp')
        tmp.write_text(nb, newline='\n')
        os.replace(tmp, bs)  # atomic: a running build keeps reading the old inode
        print('build script: chained keitai-apps')
    else:
        print('WARN could not chain keitai-apps into the build script')
print('keitai apps staged')

# ------------------------------------------------------------------------------------------------ Home: pin the Messages tile
# Live finding: with equal intent-filter priority (apps installed in /data) CATEGORY_APP_MESSAGING resolves to the chooser.
OLD = 'addFixed(pm, seen, "Messages", new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_APP_MESSAGING));'
NEW = ('addFixed(pm, seen, "Messages", new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_APP_MESSAGING)'
       '.setPackage(installed(pm, "org.kyf37.messages") ? "org.kyf37.messages" : null));')
HELPER = '''    private static boolean installed(PackageManager pm, String pkg) {
        try { pm.getPackageInfo(pkg, 0); return true; } catch (PackageManager.NameNotFoundException e) { return false; }
    }

'''
for home in [ROOT / 'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java', WS / 'device-inspection/Kyf37Home.java.txt']:
    if not home.exists():
        continue
    h = home.read_text()
    if 'installed(pm, "org.kyf37.messages")' in h or OLD not in h:
        continue
    h = h.replace(OLD, NEW, 1).replace('    private void hideLegacy(', HELPER + '    private void hideLegacy(', 1)
    home.write_text(h)
    print('Home messages tile pinned:', home)

# Contacts tile: same pinning (resolution picked a chooser/stock activity with a generic icon)
OLDC = 'addFixed(pm, seen, "Contacts", new Intent(Intent.ACTION_VIEW, Uri.parse("content://contacts/people")));'
NEWC = ('addFixed(pm, seen, "Contacts", new Intent(Intent.ACTION_VIEW, Uri.parse("content://contacts/people"))'
        '.setPackage(installed(pm, "org.kyf37.contacts") ? "org.kyf37.contacts" : null));')
for home in [ROOT / 'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java', WS / 'device-inspection/Kyf37Home.java.txt']:
    if not home.exists():
        continue
    h = home.read_text()
    if 'installed(pm, "org.kyf37.contacts")' in h or OLDC not in h:
        continue
    home.write_text(h.replace(OLDC, NEWC, 1))
    print('Home contacts tile pinned:', home)
