"""KYF37 keypad-navigation static audit (read-only; WSL Python 3).

Scans layout XML in the trees that make up the base system UI and reports constructs that
make a control unreachable or trap focus on a non-touch keypad phone:

  NOFOCUS   control-type view with android:focusable="false" (and not an explicit decoration)
  BLOCKS    android:descendantFocusability="blocksDescendants" (children unreachable by D-pad)
  TOUCHONLY android:focusableInTouchMode="true" on a non-editable view (touch-only focus quirk)
  NOCLICKFOCUS clickable view with explicit focusable="false"

Usage: audit-keypad-focus.py [--json out.json] [--limit N]
The report is a TRIAGE list: each hit needs a human decision (many are decorative).
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('/home/pablo/kyf37-android10')
TREES = {
    'framework-dialogs': ROOT / 'frameworks/base/core/res/res',
    'Settings': ROOT / 'packages/apps/Settings/res',
    'SettingsLib': ROOT / 'frameworks/base/packages/SettingsLib/res',
    'SystemUI': ROOT / 'frameworks/base/packages/SystemUI/res',
    'SystemUI-keyguard': ROOT / 'frameworks/base/packages/SystemUI/res-keyguard',
    'Home': ROOT / 'packages/apps/Kyf37Home/res',
    'PhoneSettings': ROOT / 'packages/apps/Kyf37PhoneSettings/res',
    'Dialer': ROOT / 'packages/apps/Dialer/java',
    'PackageInstaller': ROOT / 'packages/apps/PackageInstaller/res',
    'DocumentsUI': ROOT / 'packages/apps/DocumentsUI/res',
}
ANDROID = '{http://schemas.android.com/apk/res/android}'
CONTROLS = ('Button', 'ImageButton', 'Switch', 'CheckBox', 'RadioButton', 'SeekBar', 'Spinner',
            'EditText', 'ToggleButton', 'CheckedTextView', 'NumberPicker', 'ListView')


def attr(el, name):
    return el.attrib.get(ANDROID + name)


def scan(path, tree):
    hits = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return hits
    for el in root.iter():
        tag = el.tag.split('.')[-1] if isinstance(el.tag, str) else ''
        foc = attr(el, 'focusable')
        if foc == 'false' and (tag in CONTROLS or attr(el, 'clickable') == 'true'):
            hits.append(('NOFOCUS' if tag in CONTROLS else 'NOCLICKFOCUS', tag, attr(el, 'id') or ''))
        if attr(el, 'descendantFocusability') == 'blocksDescendants':
            hits.append(('BLOCKS', tag, attr(el, 'id') or ''))
        if attr(el, 'focusableInTouchMode') == 'true' and tag not in ('EditText', 'AutoCompleteTextView'):
            hits.append(('TOUCHONLY', tag, attr(el, 'id') or ''))
    return hits


def main():
    limit = 25
    out = None
    a = sys.argv[1:]
    if '--limit' in a:
        limit = int(a[a.index('--limit') + 1])
    if '--json' in a:
        out = a[a.index('--json') + 1]
    report = {}
    for name, base in TREES.items():
        if not base.exists():
            continue
        counts = Counter()
        files = defaultdict(list)
        n = 0
        for p in base.glob('layout*/*.xml'):
            n += 1
            for kind, tag, ident in scan(p, name):
                counts[kind] += 1
                files[kind].append('%s %s %s' % (p.relative_to(base), tag, ident))
        report[name] = {'layouts': n, 'counts': dict(counts),
                        'samples': {k: v[:limit] for k, v in files.items()}}
        print('%-20s layouts=%-5d %s' % (name, n, dict(counts)))
    if out:
        Path(out).write_text(json.dumps(report, indent=1))
        print('wrote', out)


if __name__ == '__main__':
    main()
