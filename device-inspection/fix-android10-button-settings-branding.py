from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
app=root/'packages/apps/Kyf37KeypadSettings'
p=app/'src/org/kyf37/keypad/KeypadSettings.java'
s=p.read_text().replace('Your little keypad','Button settings').replace('setTitle("Keypad settings")','setTitle("Button settings")')
p.write_text(s)
p=app/'AndroidManifest.xml'
s=p.read_text().replace('android:label="Keypad settings"','android:label="Button settings"')
if 'android:icon=' not in s:
 s=s.replace('<application ', '<application android:icon="@mipmap/ic_launcher" android:roundIcon="@mipmap/ic_launcher" ')
p.write_text(s)
p=root/'packages/apps/Settings/res/xml/top_level_settings.xml'
s=p.read_text().replace('android:key="kyf37_keypad_settings" android:title="Keypad settings"','android:key="kyf37_keypad_settings" android:title="Button settings"')
p.write_text(s)
res=app/'res'
for d in ['drawable','mipmap-anydpi','mipmap-anydpi-v26','values']:(res/d).mkdir(parents=True,exist_ok=True)
paths=[('M0,0 H108 V108 H0 Z','#F4F1E9'),
 ('M39,23 H69 Q78,23 78,32 V77 Q78,86 69,86 H39 Q30,86 30,77 V32 Q30,23 39,23 Z','#466757'),
 ('M39,26 H69 Q75,26 75,32 V76 Q75,83 69,83 H39 Q33,83 33,76 V32 Q33,26 39,26 Z','#B9CDBE'),
 ('M54,30 A12,12 0,1 1,54,54 A12,12 0,1 1,54,30 Z','#466757'),
 ('M54,36 A6,6 0,1 1,54,48 A6,6 0,1 1,54,36 Z','#FFFCF4'),
 ('M54,32 L52,35 H56 Z M54,52 L52,49 H56 Z M44,42 L47,40 V44 Z M64,42 L61,40 V44 Z','#FFFCF4')]
for y in [58,66,74]:
 for x in [38,49,60]:paths.append((f'M{x+2},{y} H{x+8} Q{x+10},{y} {x+10},{y+2} V{y+3} Q{x+10},{y+5} {x+8},{y+5} H{x+2} Q{x},{y+5} {x},{y+3} V{y+2} Q{x},{y} {x+2},{y} Z','#FFFCF4'))
paths.append(('M82,24 L84,30 L90,32 L84,34 L82,40 L80,34 L74,32 L80,30 Z','#C9AD78'))
vector='<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">\n'+''.join(f' <path android:fillColor="{color}" android:pathData="{path}"/>\n' for path,color in paths)+'</vector>\n'
(res/'drawable/button_settings_icon.xml').write_text(vector)
(res/'mipmap-anydpi/ic_launcher.xml').write_text(vector)
(res/'values/icon_colors.xml').write_text('<resources><color name="button_settings_icon_background">#F4F1E9</color></resources>\n')
(res/'mipmap-anydpi-v26/ic_launcher.xml').write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
 <background android:drawable="@color/button_settings_icon_background"/>
 <foreground android:drawable="@drawable/button_settings_icon"/>
</adaptive-icon>
''')
print('Applied Button settings title, app label, Settings entry and adaptive vector keypad icon')
