"""Idempotent theme selector, larger Home icons, and local wallpaper text contrast.

Run after the two Pastel Star icon staging scripts. WSL Python 3.
"""
from pathlib import Path
import re, shutil, subprocess, importlib.util, sys

WS=Path(__file__).resolve().parent.parent
ROOT=Path('/home/pablo/kyf37-android10')
HOME=ROOT/'packages/apps/Kyf37Home'
PHONE=ROOT/'packages/apps/Kyf37PhoneSettings'
SETTINGS=ROOT/'packages/apps/Settings'

def module():
    path=WS/'device-inspection/fix-android10-pastel-settings-icons.py'
    spec=importlib.util.spec_from_file_location('pastel_settings',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def original_icon(name):
    relative='res/drawable/'+name+'.xml'
    # Original files from the tracked Lineage trees, never the already-themed files.
    for repo in (SETTINGS,ROOT/'frameworks/base/packages/SettingsLib',ROOT/'frameworks/base'):
        rel=relative if repo!=ROOT/'frameworks/base' else 'core/res/drawable/'+name+'.xml'
        p=subprocess.run(['git','-C',str(repo),'show','HEAD:'+rel],capture_output=True,text=True)
        if p.returncode==0:return p.stdout
    # Some imported SettingsLib icons are in the frameworks/base Git project.
    p=subprocess.run(['git','-C',str(ROOT/'frameworks/base'),'show','HEAD:packages/SettingsLib/'+relative],capture_output=True,text=True)
    if p.returncode==0:return p.stdout
    raise RuntimeError('Cannot preserve original icon: '+name)

def themed_xml(standard,pastel,size):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<com.android.settings.widget.Kyf37ThemeDrawable xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:src="@drawable/%s" android:drawable="@drawable/pastel_%s"\n'
        '    android:width="%ddp" android:height="%ddp" />\n')%(standard,pastel,size,size)

def main():
    m=module()
    aliases={'ic_homepage_'+key:(name,48) for key,name in m.TOP.items()}
    aliases.update({'ic_settings_'+key:(name,24) for key,name in m.SEMANTIC.items()})
    aliases.update({key:(name,24) for key,name in m.EXTRA.items()})
    draw=SETTINGS/'res/drawable'
    for alias,(name,size) in aliases.items():
        saved='kyf37_standard_'+alias
        (draw/(saved+'.xml')).write_text(original_icon(alias))
        (draw/(alias+'.xml')).write_text(themed_xml(saved,name,size))
    # Additional preference rows use native category symbols in Standard mode.
    native={name:'ic_settings_'+key for key,name in m.SEMANTIC.items() if not key.endswith('_white')}
    native.update({'keypad':'ic_settings_gestures','generic':'ic_settings_applications',
        'bluetooth':'ic_settings_wireless','gallery':'ic_settings_display','rotation':'ic_settings_gestures'})
    used={n for rows in m.ROWS.values() for n in rows.values()}
    for name in used:
        if name in native:
            (draw/('ic_pastel_'+name+'.xml')).write_text(themed_xml('kyf37_standard_'+native[name],name,32))
    shutil.copy2(WS/'device-inspection/Kyf37ThemeDrawable.java.txt',SETTINGS/'src/com/android/settings/widget/Kyf37ThemeDrawable.java')
    sm=SETTINGS/'AndroidManifest.xml'
    sm.write_text(sm.read_text().replace('android:icon="@drawable/ic_pastel_settings"','android:icon="@mipmap/ic_launcher"',1))
    top=SETTINGS/'res/xml/top_level_settings.xml'
    s=top.read_text()
    if 'kyf37_appearance' not in s:
        s=s.replace('</PreferenceScreen>', '''    <Preference android:key="kyf37_appearance" android:title="Appearance"
        android:summary="Standard or Pastel Star icons" android:order="-79" android:icon="@drawable/ic_settings_all">
        <intent android:targetPackage="org.kyf37.phonesettings" android:targetClass="org.kyf37.phonesettings.AppearanceSettings" />
    </Preference>
</PreferenceScreen>''')
    top.write_text(s)

    shutil.copy2(WS/'device-inspection/Kyf37AppearanceSettings.java.txt',PHONE/'src/org/kyf37/phonesettings/AppearanceSettings.java')
    pm=PHONE/'AndroidManifest.xml'
    s=pm.read_text()
    if 'android.permission.WRITE_SECURE_SETTINGS' not in s:
        s=s.replace('    <uses-sdk','    <uses-permission android:name="android.permission.WRITE_SECURE_SETTINGS" />\n    <uses-sdk',1)
    if 'android:name=".AppearanceSettings"' not in s:
        s=s.replace('    </application>','        <activity android:name=".AppearanceSettings" android:label="Appearance" android:exported="true" />\n    </application>')
    s=s.replace('android:icon="@drawable/ic_pastel_phone_settings"','android:icon="@android:drawable/ic_menu_preferences"')
    pm.write_text(s)
    for p in (PHONE/'src/org/kyf37/phonesettings/PhoneSettings.java',WS/'device-inspection/Kyf37PhoneSettings.java.txt'):
        s=p.read_text()
        if 'case 14:' not in s:
            s=s.replace('R.drawable.ic_pastel_phone_settings};','R.drawable.ic_pastel_phone_settings, R.drawable.ic_pastel_settings};',1)
            s=s.replace('"Apps", "About phone" };','"Apps", "About phone", "Appearance" };',1)
            s=s.replace('                default: return "";', '                case 14: return Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==0 ? "Standard" : "Pastel Star";\n                default: return "";',1)
            s=s.replace('                case 13: open(Settings.ACTION_DEVICE_INFO_SETTINGS); break;', '                case 13: open(Settings.ACTION_DEVICE_INFO_SETTINGS); break;\n                case 14: startActivity(new Intent(PhoneSettings.this,AppearanceSettings.class)); break;',1)
        anchor='            ((android.widget.ImageView) row.findViewById(4)).setImageResource(pastelIcons[i]);'
        if 'row.findViewById(4)).setVisibility' not in s:
            assert anchor in s,p
            s=s.replace(anchor,anchor+'\n            row.findViewById(4).setVisibility(Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==0 ? View.GONE : View.VISIBLE);',1)
        p.write_text(s)

    for name in ('WallpaperContrast','ContrastMath'):
        shutil.copy2(WS/('device-inspection/Kyf37'+name+'.java.txt'),HOME/('src/org/kyf37/home/'+name+'.java'))
    for p in (HOME/'src/org/kyf37/home/Home.java',WS/'device-inspection/Kyf37Home.java.txt'):
        s=p.read_text()
        s=s.replace('(int) (48 * d), (int) (48 * d)','(int) (72 * d), (int) (72 * d)')
        s=s.replace('(int) (84 * d)', '(int) (110 * d)')
        s=s.replace('t.icon = PastelIcons.get(this, info.activityInfo.packageName);','t.icon = android.provider.Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==0\n                    ? info.loadIcon(pm) : PastelIcons.get(this, info.activityInfo.packageName);')
        if 'private WallpaperContrast wallpaperContrast;' not in s:
            s=s.replace('    private GridView grid;', '''    private GridView grid;
    private WallpaperContrast wallpaperContrast;
    private TextClock clockText,dateText;
    private boolean contrastUpdatePosted;
    private final android.database.ContentObserver themeObserver = new android.database.ContentObserver(new android.os.Handler()) {
        @Override public void onChange(boolean self) { recreate(); }
    };''',1)
            s=s.replace('        super.onCreate(state);','''        super.onCreate(state);
        wallpaperContrast=new WallpaperContrast(this,new Runnable(){ public void run(){scheduleContrast();} });''',1)
            s=s.replace('        TextClock time = new TextClock(this);','        TextClock time = new TextClock(this);\n        clockText=time;',1)
            s=s.replace('        TextClock date = new TextClock(this);','        TextClock date = new TextClock(this);\n        dateText=date;',1)
            s=s.replace('        grid.setAdapter(adapter);','''        grid.setAdapter(adapter);
        grid.setOnScrollListener(new android.widget.AbsListView.OnScrollListener(){
            public void onScrollStateChanged(android.widget.AbsListView v,int state){scheduleContrast();}
            public void onScroll(android.widget.AbsListView v,int first,int visible,int total){scheduleContrast();}
        });''',1)
            s=s.replace('            return cell;','            scheduleContrast();\n            return cell;',1)
            s=s.replace('        super.onResume();','        super.onResume();\n        wallpaperContrast.refresh();\n        scheduleContrast();',1)
            at='    private Drawable selector(float d) {'
            assert at in s
            s=s.replace(at,'''    @Override protected void onStart() {
        super.onStart();
        wallpaperContrast.start();
        getContentResolver().registerContentObserver(android.provider.Settings.Global.getUriFor("kyf37_icon_theme"),false,themeObserver);
    }
    @Override protected void onStop() {
        wallpaperContrast.stop();
        getContentResolver().unregisterContentObserver(themeObserver);
        super.onStop();
    }
    private void scheduleContrast() {
        if(grid==null||contrastUpdatePosted)return;
        contrastUpdatePosted=true;
        grid.post(new Runnable(){ public void run(){
            contrastUpdatePosted=false;
            wallpaperContrast.apply(clockText);wallpaperContrast.apply(dateText);
            for(int i=0;i<grid.getChildCount();i++)
                wallpaperContrast.apply((TextView)grid.getChildAt(i).findViewById(2));
        }});
    }

'''+at,1)
        p.write_text(s)
    hm=HOME/'AndroidManifest.xml'
    s=hm.read_text()
    if 'android.permission.READ_WALLPAPER_INTERNAL' not in s:
        s=s.replace('    <uses-sdk','    <uses-permission android:name="android.permission.READ_WALLPAPER_INTERNAL" />\n    <uses-sdk',1)
    if 'android.permission.READ_EXTERNAL_STORAGE' not in s:
        s=s.replace('    <uses-sdk','    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />\n    <uses-sdk',1)
    hm.write_text(s)
    permissions=ROOT/'device/kyocera/kyf37/permissions/privapp-permissions-kyf37-home.xml'
    permissions.write_text('''<?xml version="1.0" encoding="utf-8"?>
<permissions><privapp-permissions package="org.kyf37.home">
    <permission name="android.permission.READ_WALLPAPER_INTERNAL" />
</privapp-permissions></permissions>
''')
    dm=ROOT/'device/kyocera/kyf37/device.mk'
    s=dm.read_text()
    if 'privapp-permissions-kyf37-home.xml' not in s:
        s+='\nPRODUCT_COPY_FILES += device/kyocera/kyf37/permissions/privapp-permissions-kyf37-home.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/privapp-permissions-kyf37-home.xml\n'
    default=ROOT/'device/kyocera/kyf37/permissions/default-permissions-kyf37-home.xml'
    default.write_text('''<?xml version="1.0" encoding="utf-8"?>
<exceptions><exception package="org.kyf37.home">
    <permission name="android.permission.READ_EXTERNAL_STORAGE" fixed="false" />
</exception></exceptions>
''')
    if 'default-permissions-kyf37-home.xml' not in s:
        s+='\nPRODUCT_COPY_FILES += device/kyocera/kyf37/permissions/default-permissions-kyf37-home.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/default-permissions/default-permissions-kyf37-home.xml\n'
    dm.write_text(s)
    print('Appearance: persistent Standard/Pastel switch, original Settings artwork preserved, 72dp Home icons, local wallpaper contrast')

if __name__=='__main__':
    if '--launcher-helpers-only' in sys.argv:
        for name in ('WallpaperContrast','ContrastMath'):
            shutil.copy2(WS/('device-inspection/Kyf37'+name+'.java.txt'),HOME/('src/org/kyf37/home/'+name+'.java'))
        print('Launcher contrast helpers staged')
    else: main()
