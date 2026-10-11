"""Final keypad UI pass; run after all older UI generators. No phone writes."""
from pathlib import Path
import re
root = Path('/home/pablo/kyf37-android10')
here = Path(__file__).resolve().parent
def write(p, s):
    if not p.exists() or p.read_text() != s:
        p.write_text(s)
def edit(p, fn):
    write(p, fn(p.read_text()))
base = root / 'frameworks/base'
write(base/'core/java/android/app/Kyf37SystemKeyGuide.java',
      (here/'Kyf37SystemKeyGuide.java.txt').read_text().replace('\r',''))
def activity(s):
    anchor = '        if (win != null) win.makeActive();'
    if 'Kyf37SystemKeyGuide.install(this)' not in s:
        assert anchor in s
        s = s.replace(anchor, anchor+'\n        Kyf37SystemKeyGuide.install(this);',1)
    anchor = '        final int keyCode = event.getKeyCode();\n'
    # F1 had no shared fallback. Other keys remain owned by the policy.
    start = s.index('    public boolean dispatchKeyEvent(KeyEvent event) {')
    end = s.index('\n    }',start)
    body = s[start:end]
    if 'kyf37-guide-back' not in body:
        assert anchor in body
        body = body.replace(anchor,anchor+'''        if (keyCode == KeyEvent.KEYCODE_F1 && Kyf37SystemKeyGuide.supports(this)) { // kyf37-guide-back
            if (event.getAction() == KeyEvent.ACTION_UP && !event.isCanceled()) onBackPressed();
            return true;
        }
''',1)
        s = s[:start]+body+s[end:]
    return s
edit(base/'core/java/android/app/Activity.java',activity)
edit(base/'services/core/java/com/android/server/policy/Kyf37Navigation.java',
     lambda s:s.replace('code == KeyEvent.KEYCODE_F3 && event.getScanCode() != 61',
                        'code == KeyEvent.KEYCODE_F3'))
def focused_keys(s):
    if 'private volatile String mKyf37KeyFocusPackage;' not in s:
        anchor = '    Kyf37QuickKeys mKyf37Quick;'
        assert anchor in s
        s = s.replace(anchor,anchor+'\n    private volatile String mKyf37KeyFocusPackage;',1)
    anchor = '    public void onDefaultDisplayFocusChangedLw(WindowState newFocus) {'
    if 'mKyf37KeyFocusPackage = newFocus' not in s:
        assert anchor in s
        s = s.replace(anchor,anchor+'\n        mKyf37KeyFocusPackage = newFocus == null ? null : newFocus.getOwningPackage();',1)
    old = '''        if (mKyf37Quick != null && !isInjected && interactive
                && mKyf37Quick.intercept(event, keyguardActive)) {'''
    if '// kyf37-contextual-softkeys' not in s:
        assert old in s
        s = s.replace(old,'''        // kyf37-contextual-softkeys: app guides must receive physical corners.
        // Preserve Home quick launches, captured key releases/modifiers, and
        // the existing Clear/Call hold behavior. Focus ownership is volatile.
        if (mKyf37Quick != null && !isInjected && interactive
                && ("org.kyf37.home".equals(mKyf37KeyFocusPackage)
                    || event.getScanCode() == 355 || event.getScanCode() == 231
                    || mKyf37Quick.isPendingSoftkey(event))
                && mKyf37Quick.intercept(event, keyguardActive)) {''',1)
    return s
edit(base/'services/core/java/com/android/server/policy/PhoneWindowManager.java',focused_keys)
def captured_keys(s):
    if 'public boolean isPendingSoftkey(' not in s:
        anchor = '    public void reset() {'
        assert anchor in s
        s = s.replace(anchor,'''    /** Finish a Home-started key gesture even if its launch changes focus. */
    public boolean isPendingSoftkey(KeyEvent event) {
        int scan = event.getScanCode(), code = event.getKeyCode();
        return (scan >= SCAN_CONTACTS && scan <= SCAN_APPS && pendingLong.get(scan) != null)
                || (appsHeld && code >= KeyEvent.KEYCODE_0 && code <= KeyEvent.KEYCODE_9);
    }

'''+anchor,1)
    return s
edit(base/'services/core/java/com/android/server/policy/Kyf37QuickKeys.java',captured_keys)
def native_phone_footer(s):
    start = s.index('            LinearLayout foot = new LinearLayout(c);')
    end = s.index('\n        }',start)
    s = s[:start]+'''            LinearLayout foot = new LinearLayout(c); // kyf37-corner-guide
            foot.setTag("kyf37-corner-guide-v2");
            foot.setOrientation(LinearLayout.HORIZONTAL);
            foot.setBackgroundColor(0xFF101722);
            LinearLayout left = new LinearLayout(c), right = new LinearLayout(c);
            left.setOrientation(LinearLayout.VERTICAL); right.setOrientation(LinearLayout.VERTICAL);
            hintL = hint(c, Gravity.CENTER); hintC = hint(c, Gravity.CENTER);
            hintR = hint(c, Gravity.CENTER);
            hintR.setTextSize(10); hintR.setBackgroundColor(0xFF101722);
            final TextView camera = hint(c, Gravity.CENTER), mail = hint(c, Gravity.CENTER), browser = hint(c, Gravity.CENTER);
            camera.setText("Menu"); mail.setText("Pointer"); browser.setText("Home");
            // Native MENU and F1 share the app's context action (e.g. Save).
            hintL.addTextChangedListener(new android.text.TextWatcher() {
                public void beforeTextChanged(CharSequence text,int start,int count,int after) { }
                public void onTextChanged(CharSequence text,int start,int before,int count) { }
                public void afterTextChanged(android.text.Editable text) { camera.setText(text.toString()); }
            });
            keyChip(c, hintL, 1); keyChip(c, camera, 2); keyChip(c, mail, 3); keyChip(c, browser, 4); keyChip(c, hintC, 0);
            left.addView(hintL, cornerCell(c)); left.addView(mail, cornerCell(c));
            right.addView(camera, cornerCell(c)); right.addView(browser, cornerCell(c));
            foot.addView(left, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, .36f));
            LinearLayout.LayoutParams center = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, .28f);
            center.setMargins(px(c,3),px(c,3),px(c,3),px(c,3));
            foot.addView(hintC, center);
            foot.addView(right, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, .36f));
            root.addView(hintR, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, px(c,16)));
            root.addView(foot, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, px(c,60)));
''' + s[end:]
    anchor = '        private static TextView hint(Context c, int gravity) {'
    assert anchor in s
    if 'private static void keyChip(' not in s:
        s = s.replace(anchor,'''        private static LinearLayout.LayoutParams cornerCell(Context c) {
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1);
            p.setMargins(px(c,3),px(c,3),px(c,3),px(c,3)); return p;
        }
        private static void keyChip(Context c, TextView v, int key) {
            GradientDrawable bg = new GradientDrawable(); bg.setColor(key==0?0xFF29446A:0xFF1C2839);
            bg.setCornerRadius(px(c,key==0?16:8)); v.setBackground(bg);
            v.setTextSize(12); v.setPadding(px(c,3),0,px(c,3),0);
            if(key==0)return;
            int[] icons={0,android.R.drawable.ic_menu_myplaces,android.R.drawable.ic_menu_camera,
                android.R.drawable.ic_dialog_email,android.R.drawable.ic_menu_compass};
            android.graphics.drawable.Drawable icon=c.getDrawable(icons[key]).mutate();
            icon.setTint(0xFFEDF3FF); icon.setBounds(0,0,px(c,14),px(c,14));
            v.setCompoundDrawables(icon,null,null,null); v.setCompoundDrawablePadding(px(c,3));
        }

'''+anchor,1)
    return s
for module,pkg in [('Kyf37Dialer','dialer'),('Kyf37Messages','messages'),('Kyf37Contacts','contacts')]:
    edit(root/('packages/apps/'+module+'/src/org/kyf37/'+pkg+'/KUi.java'),native_phone_footer)
ui = base/'packages/SystemUI'
def statusbar(s):
    # Reserve the width the live indicators need; give remaining room to alerts.
    s = re.sub(r'(android:id="@\+id/system_icon_area"\s+android:layout_width=")0dp("\s+android:layout_height="match_parent"\s+android:layout_weight=")1(")',
               r'\g<1>wrap_content\g<2>0\g<3>',s)
    s = s.replace('android:textAppearance="@style/TextAppearance.StatusBar.Clock"',
                  'android:textAppearance="@style/TextAppearance.StatusBar.Clock"\n                    android:fontFamily="sans-serif-medium"') if 'android:fontFamily="sans-serif-medium"' not in s else s
    return s
edit(ui/'res/layout/status_bar.xml',statusbar)
def dimens(s):
    for name,value in {'qs_tile_height':'84dp','qs_tile_margin_horizontal':'6dp',
                       'qs_tile_margin_vertical':'6dp','notification_divider_height':'8dp'}.items():
        s = re.sub(r'(<dimen name="'+name+r'">)[^<]*(</dimen>)',
                   lambda m:m[1]+value+m[2],s)
    return s
edit(ui/'res/values/dimens.xml',dimens)
def keys(s):
    if '// kyf37-native-reply-input' not in s:
        anchor = '        int key = event.getKeyCode();'
        s = s.replace(anchor,'''        View typing = window.findFocus(); // kyf37-native-reply-input
        if (typing instanceof android.widget.EditText && typing.isShown()) {
            clear(); return false; // Typing digits must not toggle quick settings.
        }
'''+anchor,1)
    if '// kyf37-notification-actions' not in s:
        assert '        list.addAll(rows);' in s
        s = s.replace('        list.addAll(rows);','''        for (ExpandableNotificationRow row : rows) { // kyf37-notification-actions
            list.add(row);
            if (row.isExpanded()) {
                View actions = row.findViewById(com.android.internal.R.id.actions);
                ArrayList<View> buttons = new ArrayList<>();
                clickables(actions, actions, buttons);
                list.addAll(buttons);
            }
        }''',1)
        anchor = '''        select(window, next);

        if (stack != null'''
        assert anchor in s
        s = s.replace(anchor,'''        select(window, next);
        next.requestRectangleOnScreen(new Rect(0, 0, next.getWidth(), next.getHeight()));

        if (stack != null''',1)
    # Clear is the physical Back key. Use Contacts to dismiss a notification
    # instead, so Back can always close the shade.
    if '// kyf37-contacts-dismiss' not in s:
        anchor = '        int key = event.getKeyCode();'
        assert anchor in s
        s = s.replace(anchor,anchor+'\n        if (key == KeyEvent.KEYCODE_F1) key = KeyEvent.KEYCODE_DEL; // kyf37-contacts-dismiss',1)
    # Empty shade can contain only clock/alarm controls; never index past the list.
    s = s.replace('list.get(top.size())','list.get(Math.min(top.size(), list.size() - 1))')
    s = s.replace('} else if (sel instanceof ExpandableNotificationRow && event.getRepeatCount() == 0) {',
                  '} else if (sel instanceof ExpandableNotificationRow && event.getRepeatCount() == 0\n'
                  '                && (key == KeyEvent.KEYCODE_DPAD_LEFT || key == KeyEvent.KEYCODE_DPAD_RIGHT)) {')
    # Quick tiles use the same release-to-activate semantics in either shade mode.
    old = '''            if (!down) return true;
            if (event.getRepeatCount() == 0) longFired = false;
'''
    new = '''            if (!down) {
                if (!longFired && sel != null && head.contains(sel)) activate(sel);
                longFired = false;
                return true;
            }
            if (event.getRepeatCount() == 0) longFired = false;
'''
    s = s.replace(old,new)
    s = s.replace('else if (head.contains(sel) || top.contains(sel)) {',
                  'else if (head.contains(sel)) { /* activate on key release; hold opens details */ }\n                else if (top.contains(sel)) {')
    return s
edit(ui/'src/com/android/systemui/statusbar/phone/Kyf37KeitaiKeys.java',keys)
write(ui/'src/com/android/systemui/statusbar/phone/Kyf37KeitaiGuide.java', '''package com.android.systemui.statusbar.phone;
import android.app.KeyguardManager;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;
/** Persistent keypad instructions; no polling or touch target. */
public final class Kyf37KeitaiGuide extends View {
 private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
 public Kyf37KeitaiGuide(Context c, AttributeSet a) { super(c,a); setFocusable(false);
  setContentDescription("D-pad moves. OK opens. Hold OK for tile details. Camera switches quick settings. Contacts dismisses a notification. Back closes."); }
 @Override protected void onDraw(Canvas c) {
  if (getContext().getSystemService(KeyguardManager.class).isKeyguardLocked()) return;
  float d=getResources().getDisplayMetrics().density;
  c.save();c.clipRect(0,0,getWidth(),getHeight());
  p.setColor(0xff101722);c.drawRect(0,0,getWidth(),getHeight(),p);
  p.setColor(0xffedf3ff);p.setTextAlign(Paint.Align.CENTER);
  p.setTextSize(11*getResources().getDisplayMetrics().scaledDensity);
  line(c,"D-pad Move  ·  OK Open  ·  Hold OK Details",getHeight()*.30f);
  p.setColor(0xffb8cae6);
  line(c,"Contacts Dismiss  ·  Camera Switch  ·  Back Close",getHeight()*.75f);
  c.restore();
 }
 private void line(Canvas c,String text,float y) {
  float size=p.getTextSize();float width=getWidth()-16*getResources().getDisplayMetrics().density;
  if(p.measureText(text)>width)p.setTextSize(size*width/p.measureText(text));
  c.drawText(text,getWidth()/2f,y-(p.ascent()+p.descent())/2,p);p.setTextSize(size);
 }
}
''')
def guide(s):
    if '<com.android.systemui.statusbar.phone.Kyf37KeitaiGuide' in s: return s
    s = s.replace('    <!-- kyf37-keypad-polish-guide -->\n','')
    s = s.replace('android:id="@+id/qs_frame"',
                  'android:id="@+id/qs_frame"\n            android:layout_marginBottom="44dp"') if 'android:id="@+id/qs_frame"\n            android:layout_marginBottom="44dp"' not in s else s
    s = s.replace('android:layout_marginBottom="@dimen/close_handle_underlap"',
                  'android:layout_marginBottom="44dp"')
    end = '</com.android.systemui.statusbar.phone.NotificationPanelView>'
    assert end in s
    return s.replace(end,'''    <!-- kyf37-keypad-polish-guide -->
    <com.android.systemui.statusbar.phone.Kyf37KeitaiGuide
        android:layout_width="match_parent" android:layout_height="40dp"
        android:layout_gravity="bottom" />
'''+end)
edit(ui/'res/layout/status_bar_expanded.xml',guide)
print('System activity guide, physical pointer key and compact shade staged')
