"""KYF37 stage 2/4: app-level keypad focus look + navigation defaults. Idempotent; WSL Python 3.

 * Home / Phone settings / Outer-screen settings: when the framework focus theme exists
   (android.view.Kyf37FocusTheme) their private blue/yellow selectors are switched off so the themed
   outline is the only selection look; on older ROMs the legacy selector stays (selection visible).
 * Appearance page (shared by Settings > Appearance and Phone settings > Appearance) gets the
   selection-colour theme (Settings.Global kyf37_focus_theme).
 * config_defaultInTouchMode=false: windows start in keypad (non-touch) mode so the first
   focus is visible on open; touch/pointer events still switch to touch mode.
"""
from pathlib import Path
import re, shutil

WS = Path(__file__).resolve().parent.parent
ROOT = Path('/home/pablo/kyf37-android10')
PH = ROOT / 'packages/apps/Kyf37PhoneSettings'
HOME = ROOT / 'packages/apps/Kyf37Home'
NL = chr(10)


def edit(paths, fn):
    for p in paths:
        if p.exists():
            s = p.read_text()
            n = fn(s)
            if n != s:
                p.write_text(n)
                print('patched', p.name)


HOME_SEL_OLD = re.compile(r'    private Drawable selector\(float d\) \{.*?\n    \}\n', re.S)
HOME_SEL_NEW = '''    private Drawable selector(float d) {
        // With the focus-theme framework the themed outline (android.view.Kyf37FocusTheme) is the
        // only selection look; on older ROMs keep the legacy blue selector so focus stays visible.
        if (Kyf37FocusCompat.has()) return new ColorDrawable(Color.TRANSPARENT);
        GradientDrawable focused = new GradientDrawable();
        focused.setColor(0x553D8BFF);
        focused.setStroke((int) (2 * d), 0xFF6AA9FF);
        focused.setCornerRadius(10 * d);
        StateListDrawable s = new StateListDrawable();
        s.addState(new int[] { android.R.attr.state_pressed }, focused);
        s.addState(new int[] { android.R.attr.state_focused }, focused);
        s.addState(new int[] { android.R.attr.state_selected }, focused);
        s.addState(new int[] {}, new ColorDrawable(Color.TRANSPARENT));
        return s;
    }
'''


def home(s):
    if 'Kyf37FocusCompat.has()' in s:
        return s
    return HOME_SEL_OLD.sub(lambda m: HOME_SEL_NEW, s, count=1)


edit([HOME / 'src/org/kyf37/home/Home.java', WS / 'device-inspection/Kyf37Home.java.txt'], home)


def phone(s):
    for old in ('new android.graphics.drawable.ColorDrawable(0x553D8BFF)',
                'new android.graphics.drawable.ColorDrawable(0)'):
        s = s.replace('list.setSelector(' + old + ')',
                      'list.setSelector(new android.graphics.drawable.ColorDrawable('
                      'Kyf37FocusCompat.has() ? 0 : 0x553D8BFF))')
    return s


edit([PH / 'src/org/kyf37/phonesettings/PhoneSettings.java',
      WS / 'device-inspection/Kyf37PhoneSettings.java.txt'], phone)

FOCUSED_LINE = '            bg.addState(new int[] {android.R.attr.state_focused}, focused);'
GUARDED_LINE = '            if (!Kyf37FocusCompat.has()) bg.addState(new int[] {android.R.attr.state_focused}, focused);'
NORMAL_LINE = '            bg.addState(new int[] {}, normal);'


def outer(s):
    if 'Kyf37FocusCompat.has()' in s:
        return s
    if FOCUSED_LINE in s:
        return s.replace(FOCUSED_LINE, GUARDED_LINE)
    return s.replace(NORMAL_LINE, GUARDED_LINE + NL + NORMAL_LINE, 1)   # earlier revision removed it


edit([PH / 'src/org/kyf37/phonesettings/OuterScreenSettings.java',
      WS / 'device-inspection/Kyf37OuterScreenSettings.java.txt'], outer)

# Same compat helper in both apps (package substituted).
for pkg, d in (('org.kyf37.phonesettings', PH / 'src/org/kyf37/phonesettings'),
               ('org.kyf37.home', HOME / 'src/org/kyf37/home')):
    if d.exists():
        (d / 'Kyf37FocusCompat.java').write_text(
            (WS / 'device-inspection/Kyf37FocusCompat.java.txt').read_text().replace('@PKG@', pkg))

shutil.copy2(WS / 'device-inspection/Kyf37AppearanceSettings.java.txt',
             PH / 'src/org/kyf37/phonesettings/AppearanceSettings.java')
top = ROOT / 'packages/apps/Settings/res/xml/top_level_settings.xml'
if top.exists():
    s = top.read_text()
    n = s.replace('android:summary="Standard or Pastel Star icons"',
                  'android:summary="Icons and selection colour"')
    if n != s:
        top.write_text(n)
        print('Settings > Appearance summary updated')

ov = ROOT / 'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_keypad_nav.xml'
ov.write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Keypad-only phone: start every window in non-touch mode so the first focus is visible. -->
    <bool name="config_defaultInTouchMode">false</bool>
    <!-- Date/time pickers: spinner (NumberPicker, D-pad + digits) instead of touch calendar/clock.
         Values: MODE_SPINNER=1, MODE_CALENDAR/CLOCK=2. -->
    <integer name="date_picker_mode_material">1</integer>
    <integer name="time_picker_mode_material">1</integer>
</resources>
''')
print('overlay: non-touch start + spinner date/time pickers written')
