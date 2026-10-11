#!/usr/bin/env python3
"""Show the system wallpaper in KYF37 Home and stage the owner's wallpaper.

Run in WSL. Apply to a running phone after installing the rebuilt Home APK:
adb shell am start -n org.kyf37.home/.WallpaperSetup
This explicitly sets both wallpapers; normal Home launches never reset them.
"""
from pathlib import Path
import shutil

ws = Path(__file__).resolve().parent
tree = Path.home() / 'kyf37-android10'
app = tree / 'packages/apps/Kyf37Home'
for path in [app / 'src/org/kyf37/home/Home.java', ws / 'Kyf37Home.java.txt']:
    s = path.read_text()
    s = s.replace('root.setBackgroundColor(0xFF10151B);', '''getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SHOW_WALLPAPER);
        getWindow().setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
        root.setBackgroundColor(Color.TRANSPARENT);''')
    s = s.replace('label.setTextColor(Color.WHITE);\n                label.setShadowLayer(3f * d, 0, d, 0xFF233C50);', 'label.setTextColor(Color.WHITE);')
    s = s.replace('time.setTextColor(Color.WHITE);\n        time.setShadowLayer(3f * d, 0, d, 0xFF233C50);', 'time.setTextColor(Color.WHITE);')
    s = s.replace('label.setTextColor(Color.WHITE);', '''label.setTextColor(Color.WHITE);
                label.setShadowLayer(3f * d, 0, d, 0xFF233C50);''')
    s = s.replace('time.setTextColor(Color.WHITE);', '''time.setTextColor(Color.WHITE);
        time.setShadowLayer(3f * d, 0, d, 0xFF233C50);''')
    s = s.replace('date.setTextColor(0xFFB8C2CC);', '''date.setTextColor(Color.WHITE);
        date.setShadowLayer(3f * d, 0, d, 0xFF233C50);''')
    path.write_text(s)

manifest = app / 'AndroidManifest.xml'
s = manifest.read_text()
if 'android.permission.SET_WALLPAPER' not in s:
    s = s.replace('    <uses-sdk', '    <uses-permission android:name="android.permission.SET_WALLPAPER" />\n    <uses-sdk')
if 'android.permission.SET_WALLPAPER_HINTS' not in s:
    s = s.replace('    <uses-sdk', '    <uses-permission android:name="android.permission.SET_WALLPAPER_HINTS" />\n    <uses-sdk')
if 'android:name=".WallpaperSetup"' not in s:
    s = s.replace('    </application>', '''        <activity android:name=".WallpaperSetup" android:exported="true"
            android:theme="@android:style/Theme.NoDisplay" />
    </application>''')
manifest.write_text(s)
(app / 'src/org/kyf37/home/WallpaperSetup.java').write_text('''package org.kyf37.home;
public final class WallpaperSetup extends android.app.Activity {
    @Override public void onCreate(android.os.Bundle state) {
        super.onCreate(state);
        try (java.io.InputStream image = getAssets().open("owner-wallpaper.png")) {
            android.app.WallpaperManager wm = android.app.WallpaperManager.getInstance(this);
            wm.suggestDesiredDimensions(480, 854);
            int id = wm.setStream(image, new android.graphics.Rect(0, 0, 480, 854), true,
                    android.app.WallpaperManager.FLAG_SYSTEM | android.app.WallpaperManager.FLAG_LOCK);
            android.util.Log.i("Kyf37Wallpaper", "Applied home and lock wallpaper id=" + id);
        } catch (java.io.IOException | RuntimeException e) {
            android.util.Log.e("Kyf37Wallpaper", "Wallpaper setup failed", e);
        }
        finish();
    }
}
''')
(app / 'assets').mkdir(exist_ok=True)
shutil.copyfile(ws / 'wallpaper/owner-wallpaper.png', app / 'assets/owner-wallpaper.png')
overlay = tree / 'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/drawable-nodpi'
overlay.mkdir(parents=True, exist_ok=True)
shutil.copyfile(ws / 'wallpaper/owner-wallpaper.png', overlay / 'default_wallpaper.png')
print('Home wallpaper support, explicit dual-wallpaper setter, and ROM default staged')
