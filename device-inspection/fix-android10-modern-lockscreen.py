#!/usr/bin/env python3
"""Modern native keyguard with a wallpaper-tonal card and physical-key navigation."""
from pathlib import Path
import re
root = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
here = Path(__file__).resolve().parent
def write(p, s):
    if not p.exists() or p.read_text() != s:
        p.write_text(s)
for name, package in [('Kyf37LockActions','com/android/keyguard'),
                      ('Kyf37LockscreenKeys','com/android/systemui/statusbar/phone')]:
    write(root / 'src' / package / (name + '.java'), (here / (name + '.java.txt')).read_text())
for p in root.glob('res*/layout/keyguard_clock_switch.xml'):
    s = p.read_text()
    s = s.replace('android:padding="18dp"', 'android:padding="12dp"')
    s = s.replace('android:fontFamily="sans-serif-light"', 'android:fontFamily="sans-serif-medium"')
    if 'com.android.keyguard.Kyf37LockActions' not in s:
        s = s.replace('</com.android.keyguard.KeyguardClockSwitch>', '''    <com.android.keyguard.Kyf37LockActions
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_below="@id/keyguard_status_area"
        android:layout_marginTop="12dp" />
</com.android.keyguard.KeyguardClockSwitch>''')
    write(p, s)
for p in root.glob('res*/values*/dimens.xml'):
    s = p.read_text()
    s = re.sub(r'(<dimen name="widget_big_font_size">)[^<]+', r'\g<1>54sp', s)
    write(p, s)
for p in root.glob('res*/layout/keyguard_status_view.xml'):
    s = p.read_text()
    if 'layout_marginStart="16dp"' not in s:
        s = s.replace('layout="@layout/keyguard_clock_switch"',
                      'layout="@layout/keyguard_clock_switch"\n            android:layout_marginStart="16dp"\n            android:layout_marginEnd="16dp"')
    s = s.replace('android:layout_height="@dimen/notification_shelf_height"', 'android:layout_height="0dp"')
    s = s.replace('android:layout_marginTop="@dimen/widget_vertical_padding"', 'android:layout_marginTop="0dp"')
    write(p, s)
p = root / 'src/com/android/keyguard/KeyguardClockSwitch.java'
s = p.read_text()
anchor = '        mClockView = findViewById(R.id.default_clock_view);'
if '// KYF37 modern clock' not in s:
    s = s.replace(anchor, anchor + '''
        // KYF37 modern clock: fixed readable scale on the 320dp handset.
        mClockView.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 54);
        mClockView.setTypeface(android.graphics.Typeface.create("sans-serif-medium", 0));
        mClockView.setLetterSpacing(-0.045f);
        mClockView.setShadowLayer(0, 0, 0, android.graphics.Color.TRANSPARENT);''')
s = s.replace('COMPLEX_UNIT_SP, 64);', 'COMPLEX_UNIT_SP, 54);')
write(p, s)
p = root / 'src/com/android/systemui/statusbar/phone/StatusBarWindowView.java'
s = p.read_text()
anchor = '    private final Kyf37KeitaiKeys mKyf37KeitaiKeys = new Kyf37KeitaiKeys();'
if 'mKyf37LockscreenKeys =' not in s:
    s = s.replace(anchor, anchor + '\n    private final Kyf37LockscreenKeys mKyf37LockscreenKeys = new Kyf37LockscreenKeys();')
anchor = '        // Only unlocked shade keys; Keyguard keeps its authentication and privacy.'
if '// KYF37 modern native lock controls' not in s:
    assert anchor in s
    s = s.replace(anchor, '''        // KYF37 modern native lock controls: never intercept credential input.
        if (android.os.Build.DEVICE.equals("kyf37")
                && mStatusBarStateController.getState() == com.android.systemui.statusbar.StatusBarState.KEYGUARD
                && !mService.isBouncerShowing()
                && !mService.isDozing()
                && mKyf37LockscreenKeys.handle(this, event, () -> mService.onSpacePressed())) return true;
''' + anchor)
s = s.replace('mKyf37LockscreenKeys.handle(this, event, () -> mService.onSpacePressed())',
              '''mKyf37LockscreenKeys.handle(this, event, () -> mService.onSpacePressed(),
                    row -> mService.dismissKeyguardThenExecute(() -> {
                        post(() -> row.performClick());
                        return false;
                    }, null, true))''')
s = s.replace('post(() -> row.performClick());', 'post(() -> mService.kyf37OpenLockNotification(row));')
write(p, s)
p = root / 'src/com/android/systemui/statusbar/phone/StatusBar.java'
s = p.read_text()
if 'void kyf37OpenLockNotification(' not in s:
    anchor = '    public void readyForKeyguardDone() {'
    assert anchor in s
    s = s.replace(anchor, '''    // Keypad activation uses the full native notification launch/work-profile pipeline.
    void kyf37OpenLockNotification(View view) {
        if (view instanceof ExpandableNotificationRow) {
            ExpandableNotificationRow row = (ExpandableNotificationRow) view;
            mNotificationActivityStarter.onNotificationClicked(row.getStatusBarNotification(), row);
        }
    }

''' + anchor)
write(p, s)
p = root / 'src/com/android/systemui/statusbar/phone/KeyguardClockPositionAlgorithm.java'
s = p.read_text()
old = '        return mHeight / 2 - mKeyguardStatusHeight - mClockNotificationsMargin;'
if '// KYF37: tall keypad card' not in s:
    assert old in s
    s = s.replace(old, '''        // KYF37: tall keypad card must not get negative Y and zero clock alpha.
        int y = mHeight / 2 - mKeyguardStatusHeight - mClockNotificationsMargin;
        return android.os.Build.DEVICE.equals("kyf37") ? Math.max(mMinTopMargin, y) : y;''')
write(p, s)
p = root / 'src/com/android/systemui/statusbar/phone/NotificationPanelView.java'
s = p.read_text()
old = '''                    (int) (mKeyguardStatusView.getHeight()
                            - mShelfHeight / 2.0f - mDarkIconSize / 2.0f),'''
if '// KYF37 card has no reserved icon shelf' not in s:
    assert old in s
    s = s.replace(old, '''                    // KYF37 card has no reserved icon shelf to subtract.
                    android.os.Build.DEVICE.equals("kyf37") ? mKeyguardStatusView.getHeight() :
                    (int) (mKeyguardStatusView.getHeight()
                            - mShelfHeight / 2.0f - mDarkIconSize / 2.0f),''')
write(p, s)
print('Modern native lockscreen staged; authentication unchanged')
import runpy
runpy.run_path(str(here / 'fix-android10-pixel-lockscreen.py'))
