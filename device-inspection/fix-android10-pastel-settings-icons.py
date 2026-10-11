"""Idempotent Pastel Star icons for Android Settings and keypad Phone settings.

--prepare: crop the generated settings atlas using Pillow (Windows).
Default: stage resource-only Android Settings changes and Phone settings row icons (WSL).
"""
from pathlib import Path
import json, re, shutil, sys

WS = Path(__file__).resolve().parent.parent
PACK = WS/'kyf37-rom/pastel-star-icons'
TREE = Path('/home/pablo/kyf37-android10')
NAMES = '''battery display sound storage privacy system support printer
mobile_data hotspot airplane vibration usb rotation language notifications'''.split()
TOP = {
 'network':'wifi', 'connected_device':'bluetooth', 'apps':'generic',
 'battery':'battery', 'display':'display', 'sound':'sound', 'storage':'storage',
 'privacy':'privacy', 'location':'maps', 'security':'security', 'accounts':'contacts',
 'accessibility':'accessibility', 'system_dashboard':'system', 'about':'phone_settings',
 'support':'support',
}
SEMANTIC = {
 '24dp':'settings', 'about':'phone_settings', 'accessibility':'accessibility',
 'accounts':'contacts', 'adaptive_sleep':'clock', 'all':'settings', 'aod':'display',
 'applications':'generic', 'backup':'backup', 'backup_restore':'backup',
 'battery':'battery', 'battery_white':'battery', 'camera':'camera',
 'data_usage':'mobile_data', 'date_time':'clock', 'development':'tools',
 'display':'display', 'display_white':'display', 'gestures':'rotation', 'home':'home',
 'language':'language', 'location':'maps', 'memory':'storage', 'multiuser':'contacts',
 'nfc_payment':'wallet', 'night_display':'display', 'personal':'contacts',
 'phone_idle':'phone', 'print':'printer', 'privacy':'privacy',
 'security':'security', 'security_white':'security', 'sign_in':'contacts',
 'sim':'sim', 'sound':'sound', 'sync':'update', 'system_dashboard_white':'system',
 'voice_calls':'phone', 'wireless':'wifi', 'wireless_white':'wifi',
}
EXTRA = {
 'ic_network_cell':'mobile_data', 'ic_wifi_tethering':'hotspot',
 'ic_airplanemode_active':'airplane', 'ic_vpn_key':'privacy',
 'ic_volume_remote':'sound', 'ic_media_stream':'music', 'ic_local_phone_24_lib':'phone',
 'ic_audio_ring':'sound', 'ic_notifications':'notifications',
 'ring_notif_increasing':'sound', 'ic_restore':'backup', 'ic_system_update':'update',
}
# Add illustrations to existing rows without altering their controllers or behavior.
ROWS = {
 'top_level_settings.xml': {'kyf37_keypad_settings':'keypad'},
 'display_settings.xml': {
   'brightness':'display', 'dark_ui_mode':'display', 'night_display':'display',
   'auto_brightness_entry':'display', 'wallpaper':'gallery', 'screen_timeout':'clock',
   'auto_rotate':'rotation', 'font_size':'language', 'display_settings_screen_zoom':'display',
 },
 'connected_devices.xml': {'add_bt_devices':'bluetooth', 'connection_preferences':'bluetooth'},
 'connected_devices_advanced.xml': {'bluetooth':'bluetooth', 'usb':'usb', 'nfc':'wallet', 'print':'printer'},
 'system_dashboard_fragment.xml': {'language_input':'language', 'date_time':'clock'},
}
PHONE = 'wifi bluetooth sound display clock clock language battery keypad settings sound storage generic phone_settings'.split()

def prepare():
    from PIL import Image, ImageDraw
    atlas = Image.open(PACK/'settings-atlas.png').convert('RGBA')
    assert atlas.getextrema()[3][0] == 0
    # Minimum alpha projections locate the transparent gutters of this 4×4 atlas.
    alpha = atlas.getchannel('A')
    def cuts(vertical):
        size = atlas.width if vertical else atlas.height
        projection = [sum(alpha.crop((i,0,i+1,atlas.height) if vertical else (0,i,atlas.width,i+1)).getdata()) for i in range(size)]
        result = [0]
        for k in range(1,4):
            lo,hi = round((k-.2)*size/4),round((k+.2)*size/4)
            result.append(min(range(lo,hi),key=lambda i:projection[i]))
        return result+[size]
    xs,ys = cuts(True),cuts(False)
    out = PACK/'settings-icons'
    out.mkdir(exist_ok=True)
    preview = Image.new('RGB',(4*192,4*216),'#fff0f3')
    draw = ImageDraw.Draw(preview)
    for i,name in enumerate(NAMES):
        x,y = i%4,i//4
        tile = atlas.crop((xs[x],ys[y],xs[x+1],ys[y+1]))
        tile = tile.crop(tile.getbbox())
        tile.thumbnail((164,164),Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA',(192,192))
        canvas.paste(tile,((192-tile.width)//2,(192-tile.height)//2))
        canvas.save(out/('pastel_'+name+'.png'))
        preview.paste(canvas,(x*192,y*216),canvas)
        draw.text((x*192+12,y*216+194),name.replace('_',' '),fill='#884b60')
    preview.save(PACK/'settings-preview.png')
    print('Prepared 16 Settings illustrations; crop boundaries',xs,ys)

def wrapper(name,size):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
            '    <item android:width="%ddp" android:height="%ddp" android:drawable="@drawable/pastel_%s" />\n'
            '</layer-list>\n') % (size,size,name)

def apply():
    settings = TREE/'packages/apps/Settings'
    phone = TREE/'packages/apps/Kyf37PhoneSettings'
    aliases = {'ic_homepage_'+key:(name,48) for key,name in TOP.items()}
    aliases.update({'ic_settings_'+key:(name,24) for key,name in SEMANTIC.items()})
    aliases.update({key:(name,24) for key,name in EXTRA.items()})
    used = set(n for n,size in aliases.values()) | set(PHONE) | {'phone_settings','settings'}
    used |= {n for rows in ROWS.values() for n in rows.values()}
    for app in (settings,phone):
        draw = app/'res/drawable'
        png = app/'res/drawable-nodpi'
        png.mkdir(parents=True,exist_ok=True)
        draw.mkdir(parents=True,exist_ok=True)
        for name in sorted(used):
            filename = 'pastel_'+name+'.png'
            source = PACK/'settings-icons'/filename
            if not source.exists(): source = PACK/'icons'/filename
            assert source.is_file(), source
            shutil.copy2(source,png/filename)
            (draw/('ic_pastel_'+name+'.xml')).write_text(wrapper(name,32))
    for key,(name,size) in sorted(aliases.items()):
        (settings/'res/drawable'/(key+'.xml')).write_text(wrapper(name,size))
    changed_rows = []
    for filename,rows in ROWS.items():
        p = settings/'res/xml'/filename
        if not p.exists(): continue
        s = p.read_text()
        for key,name in rows.items():
            pattern = r'(<[\w.]+\s[^>]*\bandroid:key="'+re.escape(key)+r'"[^>]*?)(\s*/?>)'
            def repl(m):
                prefix = re.sub(r'\s+android:icon="[^"]*"','',m.group(1))
                return prefix+' android:icon="@drawable/ic_pastel_'+name+'"'+m.group(2)
            s,count = re.subn(pattern,repl,s,count=1)
            if count: changed_rows.append(filename+':'+key)
        p.write_text(s)
    sm = settings/'AndroidManifest.xml'
    s = sm.read_text().replace('android:icon="@mipmap/ic_launcher"','android:icon="@drawable/ic_pastel_settings"',1)
    sm.write_text(s)
    for p in (phone/'src/org/kyf37/phonesettings/PhoneSettings.java',WS/'device-inspection/Kyf37PhoneSettings.java.txt'):
        s = p.read_text()
        if 'private final int[] pastelIcons' not in s:
            icons = ', '.join('R.drawable.ic_pastel_'+n for n in PHONE)
            s = s.replace('    private ListView list;', '    private final int[] pastelIcons = {'+icons+'};\n    private ListView list;',1)
            anchor = '                LinearLayout text = new LinearLayout(PhoneSettings.this);'
            assert s.count(anchor)==1,p
            s = s.replace(anchor,'''                android.widget.ImageView image = new android.widget.ImageView(PhoneSettings.this);
                image.setId(4);
                LinearLayout.LayoutParams iconLp = new LinearLayout.LayoutParams((int)(32*d),(int)(32*d));
                iconLp.rightMargin = (int)(10*d);
                row.addView(image, iconLp);
'''+anchor,1)
            anchor = '            title.setText(titles[i]);'
            assert s.count(anchor)==1,p
            s = s.replace(anchor,'''            ((android.widget.ImageView) row.findViewById(4)).setImageResource(pastelIcons[i]);
'''+anchor,1)
        p.write_text(s)
    pm = phone/'AndroidManifest.xml'
    s = pm.read_text()
    if 'android:icon=' not in s:
        s = s.replace('<application ', '<application android:icon="@drawable/ic_pastel_phone_settings" ',1)
    pm.write_text(s)
    coverage = {'settings_resource_aliases':len(aliases),'homepage_categories':len(TOP),
                'extra_preference_rows':changed_rows,'phone_settings_rows':len(PHONE),
                'additional_icons':len(NAMES),'runtime_behavior_changes':False}
    (PACK/'settings-coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    print(json.dumps(coverage,indent=2))

if __name__ == '__main__':
    if '--prepare' in sys.argv: prepare()
    else: apply()
