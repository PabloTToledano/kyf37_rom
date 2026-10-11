"""Final ROM UI policy: app-owned Kyocera softkeys, no generic footer or home clock.

Run after older UI staging scripts; also enforced before every ROM build.
"""
from pathlib import Path
import re
root=Path('/home/pablo/kyf37-android10')
def write(p,s):
 if not p.exists() or p.read_text()!=s:p.write_text(s)
p=root/'frameworks/base/packages/SystemUI/src/com/android/systemui/statusbar/phone/NavigationBarView.java'
s=p.read_text()
s=re.sub(r'        if \("kyf37"\.equals\(android\.os\.Build\.DEVICE\)\) \{\s*mNavigationInflaterView\.setVisibility\(View\.INVISIBLE\);\s*addView\(new Kyf37SoftkeyBar\(getContext\(\)\), new android\.widget\.FrameLayout\.LayoutParams\(\s*android\.view\.ViewGroup\.LayoutParams\.MATCH_PARENT,\s*android\.view\.ViewGroup\.LayoutParams\.MATCH_PARENT\)\);\s*\}', '',s)
assert 'new Kyf37SoftkeyBar' not in s, 'Unexpected generic footer insertion'
write(p,s)
p=root/'frameworks/base/services/core/java/com/android/server/wm/DisplayPolicy.java'
s=p.read_text()
anchor='''            } else if ("0".equals(navBarOverride)) {
                mHasNavigationBar = true;
            }'''
assert anchor in s
override='''
            // KYF37 uses physical keys and app-owned Kyocera softkeys.
            if ("kyf37".equals(android.os.Build.DEVICE)) mHasNavigationBar = false;'''
if override not in s:s=s.replace(anchor,anchor+override,1)
write(p,s)
p=root/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_softkey_dimensions.xml'
write(p,'''<resources>
    <!-- Physical keys supply navigation; Kyocera apps reserve their own softkey area. -->
    <dimen name="navigation_bar_height">0dp</dimen>
    <dimen name="navigation_bar_height_landscape">0dp</dimen>
    <dimen name="navigation_bar_width">0dp</dimen>
</resources>
''')
# Disable the system navigation window itself, rather than merely drawing it blank.
p=root/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/values/kyf37_native_navigation.xml'
write(p,'<resources><bool name="config_showNavigationBar">false</bool></resources>\n')
p=root/'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
s=p.read_text()
s=re.sub(r'        TextClock time = new TextClock\(this\);.*?        header\.addView\(time\);\n','',s,flags=re.S)
s=s.replace('private TextClock clockText,dateText;','private TextClock dateText;')
s=s.replace('wallpaperContrast.apply(clockText);','')
assert 'header.addView(time)' not in s and 'clockText' not in s
write(p,s)
print('Generic navigation footer disabled; app-owned native bars retained; home clock removed')
