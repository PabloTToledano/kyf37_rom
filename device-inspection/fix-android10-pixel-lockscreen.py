"""Free-floating Pixel-inspired native clock; no authentication changes."""
from pathlib import Path
import re
r = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
def write(p, s):
    if p.read_text() != s: p.write_text(s)
for p in r.glob('res*/layout/keyguard_clock_switch.xml'):
    s = p.read_text().replace('android:background="@drawable/keitai_standby_plate"', 'android:background="@android:color/transparent"')
    s = s.replace('android:singleLine="true"', 'android:singleLine="false"')
    s = s.replace('android:padding="12dp"', 'android:padding="0dp"')
    s = s.replace('android:layout_marginTop="12dp"', 'android:layout_marginTop="8dp"')
    write(p, s)
p = r/'src/com/android/keyguard/KeyguardClockSwitch.java'
s = p.read_text()
if '// KYF37 Pixel clock' not in s:
    anchor = '    public void setTextSize(int unit, float size) {'
    assert anchor in s
    s = s.replace(anchor, '''    // KYF37 Pixel clock uses native TextClock time/user/locale updates.
    private void kyf37PixelClock() {
        if (!android.os.Build.DEVICE.equals("kyf37") || mClockView == null) return;
        mClockView.setSingleLine(false);
        mClockView.setIncludeFontPadding(false);
        mClockView.setLineSpacing(0, .86f);
        mClockView.setTypeface(android.graphics.Typeface.create("sans-serif-medium", 0));
        mClockView.setLetterSpacing(-.045f);
        mClockView.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP,
                mHasVisibleNotifications ? 62 : 104);
        mClockView.setFormat12Hour(mHasVisibleNotifications ? "h:mm" : "hh\\nmm");
        mClockView.setFormat24Hour(mHasVisibleNotifications ? "HH:mm" : "HH\\nmm");
    }

''' + anchor)
    s = s.replace('        mClockView.setTextSize(unit, size);', '        mClockView.setTextSize(unit, size);\n        kyf37PixelClock();')
    s = s.replace('        mClockViewBold.setFormat12Hour(format);', '        mClockViewBold.setFormat12Hour(format);\n        kyf37PixelClock();')
    s = s.replace('        mClockViewBold.setFormat24Hour(format);', '        mClockViewBold.setFormat24Hour(format);\n        kyf37PixelClock();')
    s = s.replace('        mHasVisibleNotifications = hasVisibleNotifications;', '        mHasVisibleNotifications = hasVisibleNotifications;\n        kyf37PixelClock();')
write(p, s)
print('Pixel-inspired stacked/compact native clock staged')
