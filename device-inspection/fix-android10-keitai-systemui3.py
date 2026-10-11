"""Keitai notification panel, pass 3. Run in WSL after fix-android10-keitai-systemui2.py.

The unlocked shade used the touch Quick Settings header (~176 dp of tiles that a keypad
cannot reach). Cover that area with a keitai info header (big time, "M/d (EEE)", unread
count) and put an opaque pale backdrop behind the flat notification list. Both views draw
only while the keyguard is not locked, so the lockscreen is untouched.
"""
from pathlib import Path

root = Path('/home/pablo/kyf37-android10/frameworks/base/packages/SystemUI')
java = root / 'src/com/android/systemui/statusbar/phone'

(java / 'Kyf37KeitaiShadeBackdrop.java').write_text('''package com.android.systemui.statusbar.phone;
import android.app.KeyguardManager;
import android.content.Context;
import android.graphics.Canvas;
import android.util.AttributeSet;
import android.view.View;
/** Opaque pale backdrop behind the unlocked notification list (keitai look). */
public final class Kyf37KeitaiShadeBackdrop extends View {
 public Kyf37KeitaiShadeBackdrop(Context c, AttributeSet a) { super(c, a); setFocusable(false); }
 @Override protected void onDraw(Canvas canvas) {
  if (getContext().getSystemService(KeyguardManager.class).isKeyguardLocked()) return;
  canvas.drawColor(0xffe6eff7);
 }
}
''')

(java / 'Kyf37KeitaiShadeHeader.java').write_text('''package com.android.systemui.statusbar.phone;
import android.app.KeyguardManager;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.util.AttributeSet;
import android.view.View;
import android.view.ViewGroup;
import com.android.systemui.R;
import com.android.systemui.statusbar.notification.row.ExpandableNotificationRow;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
/** Keitai info header: replaces the touch Quick Settings header in the unlocked shade. */
public final class Kyf37KeitaiShadeHeader extends View {
 private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
 private final Runnable tick = new Runnable() {
  @Override public void run() { invalidate(); postDelayed(this, 5000); }
 };
 public Kyf37KeitaiShadeHeader(Context c, AttributeSet a) { super(c, a); setFocusable(false); }
 @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); post(tick); }
 @Override protected void onDetachedFromWindow() { removeCallbacks(tick); super.onDetachedFromWindow(); }
 private int count() {
  View stack = getRootView().findViewById(R.id.notification_stack_scroller);
  if (!(stack instanceof ViewGroup)) return 0;
  int n = 0; ViewGroup g = (ViewGroup) stack;
  for (int i = 0; i < g.getChildCount(); i++)
   if (g.getChildAt(i) instanceof ExpandableNotificationRow
     && g.getChildAt(i).getVisibility() == View.VISIBLE) n++;
  return n;
 }
 @Override protected void onDraw(Canvas canvas) {
  if (getContext().getSystemService(KeyguardManager.class).isKeyguardLocked()) return;
  float d = getResources().getDisplayMetrics().density, w = getWidth(), h = getHeight();
  paint.setColor(0xff142638); canvas.drawRect(0, 0, w, h, paint);
  paint.setColor(0xffb4d7ef); canvas.drawRect(0, h - 3 * d, w, h, paint);
  Date now = new Date();
  paint.setTypeface(Typeface.MONOSPACE); paint.setColor(0xffffffff);
  paint.setTextAlign(Paint.Align.LEFT); paint.setTextSize(44 * d);
  canvas.drawText(new SimpleDateFormat("HH:mm", Locale.getDefault()).format(now), 14 * d, h * 0.55f, paint);
  paint.setTypeface(Typeface.DEFAULT); paint.setColor(0xffb4d7ef); paint.setTextSize(16 * d);
  canvas.drawText(new SimpleDateFormat("M/d (EEE)", Locale.getDefault()).format(now), 16 * d, h * 0.82f, paint);
  int n = count();
  paint.setTextAlign(Paint.Align.RIGHT); paint.setColor(0xffffffff); paint.setTextSize(15 * d);
  canvas.drawText("Notifications", w - 14 * d, h * 0.40f, paint);
  paint.setTextSize(30 * d); paint.setTypeface(Typeface.DEFAULT_BOLD);
  paint.setColor(n > 0 ? 0xffffd35a : 0xff8fa8bf);
  canvas.drawText(n > 0 ? String.valueOf(n) : "none", w - 14 * d, h * 0.80f, paint);
  setContentDescription(n + " notifications");
 }
}
''')

p = root / 'res/layout/status_bar_expanded.xml'
s = p.read_text()
if 'keitai_shade_backdrop' not in s:
    marker = '    <FrameLayout\n        android:id="@+id/big_clock_container"'
    assert marker in s
    s = s.replace(marker, '''    <com.android.systemui.statusbar.phone.Kyf37KeitaiShadeBackdrop
        android:id="@+id/keitai_shade_backdrop"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

''' + marker, 1)
if 'keitai_shade_header' not in s:
    marker = '    <com.android.systemui.statusbar.phone.Kyf37KeitaiGuide'
    assert marker in s
    s = s.replace(marker, '''    <com.android.systemui.statusbar.phone.Kyf37KeitaiShadeHeader
        android:id="@+id/keitai_shade_header"
        android:layout_width="match_parent"
        android:layout_height="152dp"
        android:layout_gravity="top"
        android:layout_marginTop="24dp" />

''' + marker, 1)
p.write_text(s)
print('Keitai SystemUI pass 3 staged')
