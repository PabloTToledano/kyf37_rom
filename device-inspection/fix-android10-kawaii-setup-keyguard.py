"""Kawaii native setup, physical SIM keypad and a quiet bottom unlock hint. WSL, rerunnable."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
here=Path(__file__).resolve().parent
root=Path('/home/pablo/kyf37-android10')
sw=root/'packages/apps/SetupWizard'
ui=root/'frameworks/base/packages/SystemUI'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists() or p.read_text()!=s:p.write_text(s,encoding='utf-8',newline='\n')
# Palette: dark ink on light pastel surfaces, strong focus outlines retained.
p=sw/'res/values/colors.xml'; s=p.read_text()
for key,value in {'page_background':'#FFF5FA','primary_dark':'#E8D8F2','accent':'#7954A1','primary_text':'#493452','secondary_text':'#66516F','button_bar_text_enabled':'#493452','button_bar_text_disabled':'#88798F','biometric_setup_text_color':'#7954A1'}.items():
    s=re.sub(r'(<color name="'+key+r'">)[^<]+',lambda m:m[1]+value,s)
write(p,s)
write(sw/'res/drawable/kyf37_bunny.xml','''<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="96dp" android:height="96dp" android:viewportWidth="96" android:viewportHeight="96">
<path android:fillColor="#E6D7F4" android:pathData="M30,49 C12,3 39,0 40,41 L56,41 C57,0 84,3 66,49 C91,85 5,85 30,49 Z"/>
<path android:fillColor="#F3BED3" android:pathData="M30,21 Q29,12 33,21 L37,40 L33,40 Z M63,21 Q67,12 66,21 L62,40 L58,40 Z"/>
<path android:fillColor="#493452" android:pathData="M35,55 a3,3 0,1 0,6 0 a3,3 0,1 0,-6 0 M55,55 a3,3 0,1 0,6 0 a3,3 0,1 0,-6 0 M45,62 Q48,67 51,62 Q48,61 45,62 Z"/>
<path android:fillColor="#F3BED3" android:pathData="M25,62 a5,3 0,1 0,10 0 a5,3 0,1 0,-10 0 M61,62 a5,3 0,1 0,10 0 a5,3 0,1 0,-10 0"/>
</vector>''')
write(sw/'res/values/kyf37_setup.xml',r'''<resources>
<string name="kyf37_welcome">Hello, little flip!</string>
<string name="kyf37_intro">Let’s make this phone yours.\nLanguage · Clock · Wi-Fi · Style</string>
<string name="kyf37_keys">D-pad to move · OK to choose\nContacts / F1: next · Back: previous</string>
<string name="kyf37_style_title">A little personality</string>
<string name="kyf37_style_summary">Choose your Home icons. You can change them later in Settings.</string>
<string name="kyf37_pastel">Pastel Star — soft and sweet</string>
<string name="kyf37_sky">Sky Star — light and airy</string>
<string name="kyf37_classic">Kyocera Classic — familiar</string>
<string name="kyf37_ready">All set. Hello, world!</string>
<string name="kyf37_ready_hint">OK opens your selected app.\n* opens Home options.</string>
</resources>''')
# Keep the existing navigation bar, emergency action and completion machinery.
for name,title,summary in [('welcome_activity','kyf37_welcome','kyf37_intro'),('finish_activity','kyf37_ready','kyf37_ready_hint')]:
    p=sw/('res/layout/'+name+'.xml');s=p.read_text()
    pattern=r'<ImageView\s+android:id="@\+id/brand_logo"[\s\S]*?/>'
    card='''<ScrollView android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1" android:fillViewport="true">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:gravity="center" android:padding="24dp">
<ImageView android:id="@+id/brand_logo" android:layout_width="96dp" android:layout_height="96dp" android:src="@drawable/kyf37_bunny" android:importantForAccessibility="no"/>
<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:gravity="center" android:text="@string/'''+title+'''" android:textSize="25sp" android:textColor="#493452" android:fontFamily="sans-serif-medium"/>
<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:gravity="center" android:paddingTop="16dp" android:text="@string/'''+summary+'''" android:textSize="16sp" android:textColor="#66516F"/>
<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:gravity="center" android:paddingTop="20dp" android:text="@string/kyf37_keys" android:textSize="12sp" android:textColor="#66516F"/>
</LinearLayout></ScrollView>'''
    if '@drawable/kyf37_bunny' not in s:s,count=re.subn(pattern,card,s);assert count==1
    write(p,s)
write(sw/'src/org/lineageos/setupwizard/Kyf37AppearanceActivity.java',(here/'Kyf37AppearanceActivity.java.txt').read_text(encoding='utf-8-sig'))
write(sw/'res/layout/kyf37_appearance.xml','''<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:id="@+id/root" android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="vertical" android:background="@color/page_background">
<ScrollView android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1" android:fillViewport="true">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:padding="20dp">
<ImageView android:layout_width="64dp" android:layout_height="64dp" android:layout_gravity="center" android:src="@drawable/kyf37_bunny" android:importantForAccessibility="no"/>
<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="@string/kyf37_style_title" android:textSize="23sp" android:textColor="#493452" android:gravity="center"/>
<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="@string/kyf37_style_summary" android:textSize="14sp" android:paddingTop="8dp" android:textColor="#66516F"/>
<RadioGroup android:id="@+id/kyf37_styles" android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:paddingTop="12dp">
<RadioButton android:id="@+id/kyf37_pastel" android:layout_width="match_parent" android:layout_height="wrap_content" android:minHeight="48dp" android:text="@string/kyf37_pastel" android:focusable="true"/>
<RadioButton android:id="@+id/kyf37_sky" android:layout_width="match_parent" android:layout_height="wrap_content" android:minHeight="48dp" android:text="@string/kyf37_sky" android:focusable="true"/>
<RadioButton android:id="@+id/kyf37_classic" android:layout_width="match_parent" android:layout_height="wrap_content" android:minHeight="48dp" android:text="@string/kyf37_classic" android:focusable="true"/>
</RadioGroup>
<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="@string/kyf37_keys" android:textSize="12sp" android:paddingTop="12dp" android:textColor="#66516F"/>
</LinearLayout></ScrollView>
<com.google.android.setupdesign.view.NavigationBar android:id="@+id/navigation_bar" style="@style/SudNavBarTheme" android:layout_width="match_parent" android:layout_height="@dimen/sud_navbar_height"/>
</LinearLayout>''')
p=sw/'AndroidManifest.xml';s=p.read_text()
if '.Kyf37AppearanceActivity' not in s:
    s=s.replace('</application>','''<activity android:name=".Kyf37AppearanceActivity" android:exported="false" android:excludeFromRecents="true" android:immersive="true" android:windowSoftInputMode="stateAlwaysHidden">
<intent-filter><action android:name="org.lineageos.setupwizard.KYF37_APPEARANCE"/><category android:name="android.intent.category.DEFAULT"/></intent-filter>
</activity></application>''')
write(p,s)
p=sw/'res/raw/lineage_wizard_script.xml';s=p.read_text()
# This file is regenerated by the older setup patch each build.
s=s.replace('wizard:action="finish"','wizard:action="appearance"')
if 'id="appearance"' not in s:
    s=s.replace('    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_SETUP_COMPLETE;', '''    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.KYF37_APPEARANCE;end" id="appearance">
        <result wizard:action="finish" />
    </WizardAction>
    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_SETUP_COMPLETE;''')
else:
    s=s.replace('id="appearance">\n        <result wizard:action="appearance"','id="appearance">\n        <result wizard:action="finish"')
write(p,s)
# Preserve numeric views and their listeners: physical digits call performClick on them.
A='{http://schemas.android.com/apk/res/android}'
ET.register_namespace('android',A[1:-1]);ET.register_namespace('androidprv','http://schemas.android.com/apk/res-auto')
for p in ui.glob('res*/layout/keyguard_sim_pin_view.xml'):
    tree=ET.parse(p);r=tree.getroot()
    for parent in r.iter():
        if any(c.tag.endswith('NumPadKey') for c in parent):parent.set(A+'visibility','gone')
        if parent.get(A+'id')=='@+id/row0':
            parent.set(A+'layout_height','64dp');parent.attrib.pop(A+'layout_weight',None)
        if parent.get(A+'id')=='@+id/simPinEntry':parent.attrib.pop(A+'layout_marginRight',None)
    if not any(e.get(A+'id')=='@+id/kyf37_sim_keys' for e in r.iter()):
        holder=next(e for e in r.iter() if any(c.get(A+'id')=='@+id/row0' for c in e))
        holder.append(ET.Element('TextView',{A+'id':'@+id/kyf37_sim_keys',A+'layout_width':'match_parent',A+'layout_height':'wrap_content',A+'gravity':'center',A+'text':'@string/kyf37_sim_keys',A+'textColor':'?attr/wallpaperTextColor',A+'textSize':'14sp'}))
    write(p,ET.tostring(r,encoding='unicode'))
write(ui/'res/values/kyf37_keypad_hints.xml',r'''<resources><string name="kyf37_sim_keys">Use the phone’s number keys\nOK: confirm · Clear: delete</string></resources>''')
# Clear is Back on this handset. Limit deletion handling to the SIM PIN view.
p=ui/'src/com/android/keyguard/KeyguardSimPinView.java';s=p.read_text()
if '// KYF37 physical Clear' not in s:
    anchor='    @Override\n    public void resetState()'
    assert anchor in s
    s=s.replace(anchor,'''    // KYF37 physical Clear: edit digits without changing PIN validation.
    @Override public boolean dispatchKeyEvent(android.view.KeyEvent event) {
        if (android.os.Build.DEVICE.equals("kyf37")
                && event.getKeyCode() == android.view.KeyEvent.KEYCODE_BACK) {
            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN)
                onKeyDown(event.getKeyCode(), event);
            return true; // consume release too: do not dismiss the native SIM bouncer
        }
        return super.dispatchKeyEvent(event);
    }
    @Override public boolean onKeyDown(int keyCode, android.view.KeyEvent event) {
        if (android.os.Build.DEVICE.equals("kyf37") && keyCode == android.view.KeyEvent.KEYCODE_BACK) {
            if (mPasswordEntry.isEnabled()) mPasswordEntry.deleteLastChar();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

'''+anchor)
if 'consume release too:' not in s:
    s=s.replace('    // KYF37 physical Clear: edit digits without changing PIN validation.\n', '    // KYF37 physical Clear: edit digits without changing PIN validation.\n' + '    @Override public boolean dispatchKeyEvent(android.view.KeyEvent event) {\n        if (android.os.Build.DEVICE.equals("kyf37")\n                && event.getKeyCode() == android.view.KeyEvent.KEYCODE_BACK) {\n            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN)\n                onKeyDown(event.getKeyCode(), event);\n            return true; // consume release too: do not dismiss the native SIM bouncer\n        }\n        return super.dispatchKeyEvent(event);\n    }\n')
write(p,s)
# Move navigation surface out of the clock/status area into the bottom frame.
for p in ui.glob('res*/layout/keyguard_clock_switch.xml'):
    s=re.sub(r'\s*<com.android.keyguard.Kyf37LockActions\b[^>]*/>','',p.read_text());write(p,s)
for p in ui.glob('res*/layout/keyguard_bottom_area.xml'):
    s=p.read_text()
    if 'com.android.keyguard.Kyf37LockActions' not in s:
        s=s.replace('</com.android.systemui.statusbar.phone.KeyguardBottomAreaView>','''    <com.android.keyguard.Kyf37LockActions android:layout_width="match_parent" android:layout_height="wrap_content" android:layout_gravity="bottom|center_horizontal" android:layout_marginBottom="18dp" android:importantForAccessibility="yes"/>
</com.android.systemui.statusbar.phone.KeyguardBottomAreaView>''')
    write(p,s)
p=ui/'src/com/android/keyguard/Kyf37LockActions.java';s=p.read_text()
s=s.replace('unlock.setTextSize(17);','unlock.setTextSize(12);').replace('dp(174), dp(36)','LayoutParams.WRAP_CONTENT, dp(22)')
s=s.replace('hint.setTextSize(12);','hint.setTextSize(10);')
if '        GradientDrawable bg = new GradientDrawable();' in s:
    a=s.index('        GradientDrawable bg = new GradientDrawable();',s.index('public void selectUnlock'))
    b=s.index('        unlock.setText(value ?',a)
    s=s[:a]+'''        unlock.setTextColor(Color.WHITE);
            unlock.setAlpha(value ? .85f : .5f);
            unlock.setShadowLayer(dp(2), 0, dp(1), 0xcc000000);
            unlock.setBackground(null);
    '''+s[b:]
# Do not clear the new full-screen parent's background from a child.
s=s.replace('        if (getParent() instanceof View) ((View) getParent()).setBackground(null);','')
write(p,s)
print('Kawaii setup, physical SIM PIN entry and bottom unlock hint staged')
