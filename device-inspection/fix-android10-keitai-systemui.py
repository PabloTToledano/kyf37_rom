"""Keitai standby styling and physical-key notification list. Run in WSL."""
from pathlib import Path
import re

root = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
here = Path(__file__).resolve().parent
java = root / 'src/com/android/systemui/statusbar/phone'
(java / 'Kyf37KeitaiKeys.java').write_text((here / 'Kyf37KeitaiKeys.java.txt').read_text())
(java / 'Kyf37KeitaiGuide.java').write_text('''package com.android.systemui.statusbar.phone;
import android.app.KeyguardManager;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;
public final class Kyf37KeitaiGuide extends View {
 private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
 public Kyf37KeitaiGuide(Context c, AttributeSet a) { super(c,a); setFocusable(false); }
 @Override protected void onDraw(Canvas canvas) {
  super.onDraw(canvas);
  boolean locked = getContext().getSystemService(KeyguardManager.class).isKeyguardLocked();
  String text = locked ? "OK Unlock  ·  PIN / password if set"
    : "↑↓ Select  ·  OK Open  ·  ←→ Detail  ·  DEL Clear";
  canvas.drawColor(0xf0142638);
  paint.setColor(0xffffffff); paint.setTextAlign(Paint.Align.CENTER);
  paint.setTextSize(12 * getResources().getDisplayMetrics().scaledDensity);
  if (paint.measureText(text)>getWidth()-16) paint.setTextSize(paint.getTextSize()*(getWidth()-16)/paint.measureText(text));
  canvas.drawText(text, getWidth()/2f, (getHeight()-paint.ascent()-paint.descent())/2f, paint);
  setContentDescription(text);
 }
}
''')
p = java / 'StatusBarWindowView.java'
s = p.read_text()
if 'mKyf37KeitaiKeys = ' not in s:
    marker = '    public boolean dispatchKeyEvent(KeyEvent event) {'
    assert s.count(marker) == 1
    s = s.replace('    @Override\n'+marker,
        '    private final Kyf37KeitaiKeys mKyf37KeitaiKeys = new Kyf37KeitaiKeys();\n\n    @Override\n'+marker)
    s = s.replace(marker, marker+'''
        // Only unlocked shade keys; Keyguard keeps its authentication and privacy.
        if (android.os.Build.DEVICE.equals("kyf37")
                && mStatusBarStateController.getState() == com.android.systemui.statusbar.StatusBarState.SHADE
                && !mService.isBouncerShowing()
                && mKyf37KeitaiKeys.handle(this, event)) return true;
''')
p.write_text(s)
p = java / 'StatusBarWindowController.java'
s = p.read_text()
marker = '    private void adjustScreenOrientation(State state) {'
assert marker in s
if 'Keitai portrait panel' not in s:
    s = s.replace(marker, marker+'''
        // Keitai portrait panel; applications retain their own orientation.
        if (android.os.Build.DEVICE.equals("kyf37")
                && (state.isKeyguardShowingAndNotOccluded() || state.panelExpanded)) {
            mLpChanged.screenOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT;
            return;
        }
''')
p.write_text(s)
# Date text stays readable inside the dark standby plate, including theme changes.
p = root / 'src/com/android/keyguard/KeyguardClockSwitch.java'
s = p.read_text()
marker = '    public void setTextColor(int color) {'
if 'color = android.graphics.Color.WHITE; // Keitai plate' not in s:
    s = s.replace(marker, marker+'\n        if (android.os.Build.DEVICE.equals("kyf37")) color = android.graphics.Color.WHITE; // Keitai plate')
p.write_text(s)
p = root / 'src/com/android/keyguard/KeyguardSliceView.java'
s = p.read_text()
s = s.replace('mTextColor = textColor;', 'mTextColor = android.os.Build.DEVICE.equals("kyf37") ? Color.WHITE : textColor;')
s = s.replace('mTextColor = Utils.getColorAttrDefaultColor(mContext, R.attr.wallpaperTextColor);',
    'mTextColor = android.os.Build.DEVICE.equals("kyf37") ? Color.WHITE : Utils.getColorAttrDefaultColor(mContext, R.attr.wallpaperTextColor);')
p.write_text(s)
# Fine outlines give the notification list the framed, compact handset appearance.
p = root / 'res/drawable/notification_material_bg.xml'
s = p.read_text()
if '#667C91' not in s:
    s = s.replace('<solid android:color="@color/notification_material_background_color" />',
        '<solid android:color="@color/notification_material_background_color" />\n            <stroke android:width="1dp" android:color="#667C91" />')
p.write_text(s)

p = root / 'res-keyguard/layout/keyguard_clock_switch.xml'
s = p.read_text()
if 'keitai_standby_plate' not in s:
    s = s.replace('android:layout_gravity="center_horizontal|top">',
        'android:layout_gravity="center_horizontal|top"\n    android:padding="12dp"\n    android:background="@drawable/keitai_standby_plate">')
    s = s.replace('android:letterSpacing="0.02"', 'android:fontFamily="monospace"\n             android:letterSpacing="0.02"')
    s = s.replace('android:textColor="?attr/wallpaperTextColor"', 'android:textColor="#FFFFFF"')
p.write_text(s)
(root / 'res/drawable/keitai_standby_plate.xml').write_text('''<shape xmlns:android="http://schemas.android.com/apk/res/android">
 <solid android:color="#CC142638"/><stroke android:width="1dp" android:color="#B4D7EF"/>
 <corners android:radius="3dp"/>
</shape>
''')
p = root / 'res-keyguard/layout/keyguard_status_area.xml'
s = p.read_text().replace('android:textColor="?attr/wallpaperTextColor"', 'android:textColor="#FFFFFF"')
p.write_text(s)
# Slice row colors are assigned dynamically: retain wallpaper handling there.
p = root / 'res/values/strings.xml'
s = p.read_text().replace('<string name="keyguard_unlock">Swipe up to open</string>',
                         '<string name="keyguard_unlock">Press OK to unlock</string>')
p.write_text(s)
p = root / 'res/layout/status_bar_expanded.xml'
s = p.read_text()
if 'keitai_key_guide' not in s:
    s = s.replace('</com.android.systemui.statusbar.phone.NotificationPanelView>', '''
    <TextView
        android:id="@+id/keitai_key_guide"
        android:layout_width="match_parent"
        android:layout_height="32dp"
        android:layout_gravity="bottom"
        android:gravity="center"
        android:background="#F0142638"
        android:textColor="#FFFFFF"
        android:textSize="12sp"
        android:text="@string/keitai_key_guide"
        android:importantForAccessibility="yes" />
</com.android.systemui.statusbar.phone.NotificationPanelView>''')
p.write_text(s)
p = root / 'res/layout/status_bar_expanded.xml'
s = p.read_text().replace('<TextView\n        android:id="@+id/keitai_key_guide"',
 '<com.android.systemui.statusbar.phone.Kyf37KeitaiGuide\n        android:id="@+id/keitai_key_guide"')
if 'android:layout_marginBottom="28dp"\n        android:gravity="center"' not in s:
    s = s.replace('android:layout_gravity="bottom"\n        android:gravity="center"',
        'android:layout_gravity="bottom"\n        android:layout_marginBottom="28dp"\n        android:gravity="center"')
p.write_text(s)
p = root / 'res/layout/keyguard_bottom_area.xml'
s = p.read_text().replace('android:layout_marginBottom="@dimen/keyguard_indication_margin_bottom"',
                         'android:layout_marginBottom="66dp"')
p.write_text(s)
p = root / 'res/values/keitai.xml'
p.write_text('''<resources>
 <string name="keitai_key_guide">↑↓ Select · OK Open · ←→ Detail · DEL Clear</string>
</resources>
''')
print('Keitai SystemUI staged: clock plate, OK unlock, D-pad notification controls')
