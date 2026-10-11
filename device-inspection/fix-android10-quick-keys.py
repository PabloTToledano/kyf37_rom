"""Quick-launch keypad support (see KEYPAD.md). Idempotent; run inside WSL."""
from pathlib import Path
import re, shutil
root = Path('/home/pablo/kyf37-android10')
ws = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection')
pol = root / 'frameworks/base/services/core/java/com/android/server/policy'

# 1. New policy class (with a recents hook instead of a bogus broadcast)
src = (ws / 'Kyf37QuickKeys.java.txt').read_text()
src = src.replace('    private boolean appsHeld;', '    private Runnable recentsAction;\n    private boolean appsHeld;', 1)
src = src.replace('    /** @return true if the event was consumed', '    public void setRecents(Runnable action) { recentsAction = action; }\n\n    /** @return true if the event was consumed', 1)
src = src.replace('if (isLong) start(new Intent("com.android.systemui.recents.TOGGLE_RECENTS"), true);',
                  'if (isLong) { if (recentsAction != null) handler.post(recentsAction); }', 1)
(pol / 'Kyf37QuickKeys.java').write_text(src)

# 2. PhoneWindowManager wiring
p = pol / 'PhoneWindowManager.java'
s = p.read_text()
if 'mKyf37Quick' not in s:
    s = s.replace('    Kyf37Feedback mKyf37Feedback;', '    Kyf37Feedback mKyf37Feedback;\n    Kyf37QuickKeys mKyf37Quick;', 1)
    a = '            mKyf37Navigation = new Kyf37Navigation(context, mHandler);\n'
    assert s.count(a) == 1
    s = s.replace(a, a + '''            mKyf37Quick = new Kyf37QuickKeys(context, mHandler);
            mKyf37Quick.setRecents(new Runnable() { public void run() { toggleRecentApps(); } });
''', 1)
    a = '        if (mKyf37Navigation != null && !isInjected && event.getScanCode() > 0) {'
    assert s.count(a) == 1
    s = s.replace(a, '''        // Quick-launch keys (Contacts / Camera / Mail / Apps, Apps+digit, Clear and Call holds).
        if (mKyf37Quick != null && !isInjected && interactive
                && mKyf37Quick.intercept(event, keyguardActive)) {
            return 0;
        }

''' + a, 1)
    a = '        if (!lidOpen && mKyf37Navigation != null) mKyf37Navigation.reset();'
    assert s.count(a) == 1
    s = s.replace(a, a + '\n        if (!lidOpen && mKyf37Quick != null) mKyf37Quick.reset();', 1)
    p.write_text(s)

# 3. Pointer toggle only on the printed F3/POINT key (scan 65) or injected test events
n = pol / 'Kyf37Navigation.java'
t = n.read_text()
t = t.replace('        if (code == KeyEvent.KEYCODE_F3) {', '        if (code == KeyEvent.KEYCODE_F3 && event.getScanCode() != 61) {', 1)
n.write_text(t)

# 4. Key layout: bottom F1 = Menu, bottom F2 = Recents
kl = root / 'device/kyocera/kyf37/keylayout/matrix_keypad_67.kl'
k = kl.read_text()
k = re.sub(r'^key 63\s+\S+', 'key 63      MENU', k, flags=re.M)
k = re.sub(r'^key 64\s+\S+', 'key 64      APP_SWITCH', k, flags=re.M)
kl.write_text(k)

# 5. Soft-key legend: matches the printed keys
bar = root / 'frameworks/base/packages/SystemUI/src/com/android/systemui/statusbar/phone/Kyf37SoftkeyBar.java'
b = bar.read_text()
b = re.sub(r'String\[\] names = \{.*?\};', 'String[] names = {"F1 Menu", "F2 Recent", pointer ? "OK Click" : "OK Select",\n                pointer ? "F3 Exit" : "F3 Pointer"};', b, count=1, flags=re.S)
b = re.sub(r'float\[\] weights = \{.*?\};', 'float[] weights = {1f, 1.1f, 1.2f, 1.2f};', b, count=1, flags=re.S)
bar.write_text(b)

# 6. Keypad settings labels/defaults
ks = root / 'packages/apps/Kyf37KeypadSettings/src/org/kyf37/keypad/KeypadSettings.java'
c = ks.read_text()
c = c.replace('{131,132,133,134,187,141,133,', '{131,132,133,134,82,187,133,', 1)
c = re.sub(r'names=\{"F1","F2","Auxiliary key scan 61","F4","Extra key F5","Extra key F6","F3 \(marked pointer key\)",',
           'names={"Contacts key (quick launch)","Camera key (quick launch)","Mail key (quick launch)","Apps key (Home; hold + digit)","Bottom F1 key (Menu)","Bottom F2 key (Recents)","Bottom F3 / POINT key",', c, count=1)
ks.write_text(c)

# 7. Home grid: key 0 opens tile 10, long-press # toggles silent/vibrate
home = root / 'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
h = (ws / 'Kyf37Home.java.txt').read_text()
h = h.replace('''            if (code >= KeyEvent.KEYCODE_1 && code <= KeyEvent.KEYCODE_9) {
                int i = code - KeyEvent.KEYCODE_1;''', '''            if (code == KeyEvent.KEYCODE_POUND) { event.startTracking(); return true; }
            if ((code >= KeyEvent.KEYCODE_1 && code <= KeyEvent.KEYCODE_9) || code == KeyEvent.KEYCODE_0) {
                int i = code == KeyEvent.KEYCODE_0 ? 9 : code - KeyEvent.KEYCODE_1;''', 1)
h = h.replace('    @Override public void onBackPressed()', '''    @Override public boolean onKeyLongPress(int code, KeyEvent event) {
        if (code == KeyEvent.KEYCODE_POUND) {
            android.media.AudioManager am = (android.media.AudioManager) getSystemService(AUDIO_SERVICE);
            boolean silent = am.getRingerMode() == android.media.AudioManager.RINGER_MODE_NORMAL;
            am.setRingerMode(silent ? android.media.AudioManager.RINGER_MODE_VIBRATE
                    : android.media.AudioManager.RINGER_MODE_NORMAL);
            Toast.makeText(this, silent ? "Vibrate mode" : "Ringer on", Toast.LENGTH_SHORT).show();
            return true;
        }
        return super.onKeyLongPress(code, event);
    }

    @Override public void onBackPressed()''', 1)
h = h.replace('label.setText(position < 9 ? (position + 1) + " " + t.label : t.label);',
              'label.setText(position < 10 ? ((position + 1) % 10) + " " + t.label : t.label);', 1)
home.write_text(h)
print('quick keys installed')
