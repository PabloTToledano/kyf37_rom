"""Keep original activity icons when a launcher theme has no custom artwork."""
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
HOME = Path('/home/pablo/kyf37-android10/packages/apps/Kyf37Home/src/org/kyf37/home')

for path in (WS/'device-inspection/Kyf37PastelIcons.java.txt', HOME/'PastelIcons.java'):
    old = path.read_text()
    new = old.replace('String name = packages.getProperty(pkg, "generic");',
        'String name = packages.getProperty(pkg);\n'
        '        // Missing or placeholder mappings use the original activity icon.\n'
        '        if (name == null || "generic".equals(name)) return null;')
    new = new.replace('if (!"generic".equals(name)) return get(context, "__pastel_fallback__");\n'
                      '        return context.getDrawable(android.R.drawable.sym_def_app_icon);',
                      'return null; // Missing/broken artwork also keeps the original icon.')
    assert '__pastel_fallback__' not in new
    if new != old:
        path.write_text(new)

for path in (WS/'device-inspection/Kyf37Home.java.txt', HOME/'Home.java'):
    old = path.read_text()
    anchor = '? info.loadIcon(pm) : PastelIcons.get(this, info.activityInfo.packageName);'
    replacement = anchor + '\n        if (t.icon == null) t.icon = info.loadIcon(pm);'
    new = old.replace(replacement, anchor).replace(anchor, replacement)
    assert new.count('if (t.icon == null) t.icon = info.loadIcon(pm);') == 2
    if new != old:
        path.write_text(new)
print('Original activity icon fallback staged for all launcher themes and folders')
