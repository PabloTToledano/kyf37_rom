"""SystemUI shade + QS keypad loop (KEYPAD-NAV.md 'SystemUI shade and QS loop').
Runs LAST in the keypad-nav chain (build-kyf37-android10.sh). Idempotent.
 1. Kyf37KeitaiKeys.java <- Kyf37ShadeKeys.java.txt (selection model: status clock/alarm/ringer, header quick tiles,
    notification rows, Clear all, QS tiles with digit badges, brightness slider, footer buttons, hold-OK detail).
 2. bottom key-guide strip removed from the shade; notification footer becomes a single 'Clear all' row.
 3. notification rows no longer take Android view focus (stray outline); footer text readable; no build-number text.
 4. Kyf37KeitaiShadeBackdrop keeps the number badges on screen at rest."""
from pathlib import Path
import re
root = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
here = Path(__file__).resolve().parent


def write(p, s):
    if not p.exists() or p.read_text() != s:
        p.write_text(s)


def edit(p, fn):
    s = p.read_text()
    t = fn(s)
    if t != s:
        p.write_text(t)


# 1
write(root / 'src/com/android/systemui/statusbar/phone/Kyf37KeitaiKeys.java',
      (here / 'Kyf37ShadeKeys.java.txt').read_text().replace('\r', ''))

# 2
edit(root / 'res/layout/status_bar_expanded.xml',
     lambda s: re.sub(r'\s*<com\.android\.systemui\.statusbar\.phone\.Kyf37KeitaiGuide\b.*?/>', '', s, flags=re.S))


def footer(s):
    if 'kyf37-footer' in s:
        return s
    s = s.replace('android:id="@+id/manage_text"', 'android:id="@+id/manage_text"\n            android:visibility="gone"', 1)
    s = re.sub(r'(android:id="@\+id/dismiss_text"\s+android:layout_width=")wrap_content(")', r'\1match_parent\2', s)
    s = s.replace('android:layout_gravity="end"',
                  'android:layout_gravity="center"\n            android:gravity="center"\n            android:textSize="16sp"')
    s = s.replace('<com.android.systemui.statusbar.notification.row.FooterView',
                  '<!-- kyf37-footer -->\n<com.android.systemui.statusbar.notification.row.FooterView', 1)
    return s


edit(root / 'res/layout/status_bar_notification_footer.xml', footer)
edit(root / 'res/layout/status_bar_notification_footer.xml',
     lambda s: s.replace('android:textColor="?attr/wallpaperTextColor"', 'android:textColor="#ff14202c"'))

# 3
edit(root / 'src/com/android/systemui/statusbar/notification/row/ExpandableNotificationRow.java',
     lambda s: s.replace('setFocusable(normalChild)', 'setFocusable(false)'))
edit(root / 'res/layout/status_bar_notification_row.xml',
     lambda s: s.replace('android:focusable="true"', 'android:focusable="false"', 1))
edit(root / 'src/com/android/systemui/qs/QSFooterImpl.java',
     lambda s: s if 'kyf37-nobuild' in s else s.replace(
         'if (DevelopmentSettingsEnabler.isDevelopmentSettingsEnabled(mContext)) {\n            v.setText(',
         'if (false /* kyf37-nobuild */ && DevelopmentSettingsEnabler.isDevelopmentSettingsEnabled(mContext)) {\n            v.setText(', 1))

# 4
write(root / 'src/com/android/systemui/statusbar/phone/Kyf37KeitaiShadeBackdrop.java', '''package com.android.systemui.statusbar.phone;
import android.app.KeyguardManager;
import android.content.Context;
import android.graphics.Canvas;
import android.util.AttributeSet;
import android.view.View;
/** Opaque pale backdrop behind the unlocked notification list (keitai look); also refreshes shade number badges. */
public final class Kyf37KeitaiShadeBackdrop extends View {
 public Kyf37KeitaiShadeBackdrop(Context c, AttributeSet a) { super(c, a); setFocusable(false); }
 private final Runnable tick = new Runnable() {
  @Override public void run() { try { Kyf37KeitaiKeys.refresh(Kyf37KeitaiShadeBackdrop.this); } catch (Throwable t) { } postDelayed(this, 400); }
 };
 @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); postDelayed(tick, 400); }
 @Override protected void onDetachedFromWindow() { removeCallbacks(tick); super.onDetachedFromWindow(); }
 @Override protected void onDraw(Canvas canvas) {
  if (getContext().getSystemService(KeyguardManager.class).isKeyguardLocked()) return;
  canvas.drawColor(0xffe6eff7);
 }
}
''')
# 5. keitai QS grid: 3 columns x 3 rows per page so digits 1-9 cover a whole page (default tile set fits on one page)
def dimens(s):
    def fix(name, val):
        nonlocal s
        s = re.sub(r'(<dimen name="%s">)[^<\n]*(</dimen>)?' % name,
                   lambda m: m.group(1) + val + '</dimen>', s)
    fix('qs_tile_height', '92dp')
    fix('qs_tile_margin_vertical', '4dp')
    return s
edit(root / 'res/values/dimens.xml', dimens)
print('systemui shade keypad loop staged')
