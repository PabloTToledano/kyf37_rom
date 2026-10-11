"""Install Pastel Star artwork and package mapping into KYF37 Home (idempotent, WSL).

The generated atlas is only cropped/resized here; artwork is created by imagegen.
Run with --prepare after saving atlas.png, then without arguments to apply to AOSP.
"""
from pathlib import Path
import json, re, shutil, sys, zipfile
from xml.sax.saxutils import escape

WS = Path(__file__).resolve().parent.parent
PACK = WS / 'kyf37-rom/pastel-star-icons'
HOME = Path('/home/pablo/kyf37-android10/packages/apps/Kyf37Home')
NAMES = '''phone messages contacts camera settings gallery email clock
calendar calculator files music recorder memo flashlight qr
browser store microg infrared keypad phone_settings equalizer tv
tiktok home keyboard backup downloads video maps compass
whatsapp telegram signal discord instagram facebook youtube spotify
gmail drive google play netflix pinterest reddit snapchat
weather books notes wallet shopping health games tools
bluetooth wifi security update terminal sim accessibility generic'''.split()
GROUPS = {
 'phone': 'com.android.dialer com.android.phone com.android.server.telecom',
 'messages': 'com.android.messaging com.android.mms com.google.android.apps.messaging',
 'contacts': 'com.android.contacts com.google.android.contacts',
 'camera': 'com.android.camera2 jp.kyocera.camera com.iakmds.librecamera org.lineageos.snap net.sourceforge.opencamera',
 'settings': 'com.android.settings org.lineageos.lineageparts org.lineageos.customization',
 'gallery': 'com.android.gallery3d com.google.android.apps.photos com.simplemobiletools.gallery.pro',
 'email': 'com.android.email com.fsck.k9 eu.faircode.email com.microsoft.office.outlook',
 'clock': 'com.android.deskclock com.google.android.deskclock',
 'calendar': 'org.lineageos.etar com.android.calendar com.google.android.calendar',
 'calculator': 'com.android.calculator2 com.google.android.calculator',
 'files': 'com.android.documentsui com.android.externalstorage com.android.storagemanager com.google.android.documentsui com.google.android.apps.nbu.files',
 'music': 'org.lineageos.eleven com.android.music org.videolan.vlc',
 'recorder': 'jp.kyocera.kc_soundrecorder jp.kyocera.kc_soundrecorder.manager org.lineageos.recorder',
 'memo': 'jp.kyocera.memo jp.kyocera.providers.memo',
 'flashlight': 'jp.kyocera.mobilelight org.kyf37.flashlight',
 'qr': 'jp.kyocera.barcodereader com.google.zxing.client.android',
 'browser': 'org.lineageos.jelly com.android.browser com.android.htmlviewer com.android.webview com.android.chrome org.mozilla.firefox org.mozilla.fenix com.brave.browser',
 'store': 'com.aurora.store org.fdroid.fdroid org.fdroid.basic com.looker.droidify',
 'microg': 'com.google.android.gms com.google.android.gsf org.microg.gms org.microg.gms.ui',
 'infrared': 'com.kyocera.irda org.kyf37.irda',
 'keypad': 'org.kyf37.keypad io.github.sspanak.tt9 org.kyf37.keypadime',
 'phone_settings': 'org.kyf37.phonesettings org.kyf37.subdisplay',
 'equalizer': 'org.lineageos.audiofx',
 'tv': 'org.kyf37.tv jp.kyocera.tv jp.co.fsi.fs1seg jp.co.fsi.fsdtv jp.co.fsi.fsdtvapp com.fujitsu.fsdtv',
 'tiktok': 'com.tiktok.lite.go com.zhiliaoapp.musically com.ss.android.ugc.trill',
 'home': 'org.kyf37.home com.android.launcher3 org.lineageos.trebuchet',
 'keyboard': 'com.android.inputmethod.latin com.google.android.inputmethod.latin',
 'backup': 'com.stevesoltys.seedvault com.android.backupconfirm com.android.localtransport',
 'downloads': 'com.android.providers.downloads.ui com.android.providers.downloads',
 'video': 'com.mxtech.videoplayer.ad',
 'maps': 'com.google.android.apps.maps net.osmand net.osmand.plus',
 'compass': 'com.google.android.apps.mapslite',
 'whatsapp': 'com.whatsapp com.whatsapp.w4b',
 'telegram': 'org.telegram.messenger org.telegram.messenger.web',
 'signal': 'org.thoughtcrime.securesms',
 'discord': 'com.discord',
 'instagram': 'com.instagram.android com.instagram.lite',
 'facebook': 'com.facebook.katana com.facebook.lite com.facebook.orca',
 'youtube': 'com.google.android.youtube com.google.android.apps.youtube.music org.schabi.newpipe',
 'spotify': 'com.spotify.music com.spotify.lite',
 'gmail': 'com.google.android.gm',
 'drive': 'com.google.android.apps.docs',
 'google': 'com.google.android.googlequicksearchbox',
 'play': 'com.android.vending',
 'netflix': 'com.netflix.mediaclient',
 'pinterest': 'com.pinterest',
 'reddit': 'com.reddit.frontpage',
 'snapchat': 'com.snapchat.android',
 'weather': 'org.breezyweather org.omnirom.omnijaws',
 'books': 'com.google.android.apps.books org.geometerplus.zlibrary.ui.android',
 'notes': 'com.google.android.keep net.cozic.joplin',
 'wallet': 'com.google.android.apps.walletnfcrel',
 'shopping': 'com.amazon.mShop.android.shopping',
 'health': 'com.google.android.apps.fitness',
 'games': 'com.google.android.play.games com.android.egg',
 'tools': 'com.android.traceur',
 'bluetooth': 'com.android.bluetooth com.android.bluetoothmidiservice',
 'wifi': 'com.android.captiveportallogin com.android.hotspot2',
 'security': 'com.android.permissioncontroller com.android.packageinstaller com.android.certinstaller com.android.keychain com.android.emergency',
 'update': 'org.lineageos.updater com.android.dynsystem',
 'terminal': 'com.android.terminal com.android.shell com.termux',
 'sim': 'com.android.stk com.android.simappdialog',
 'accessibility': 'com.google.android.marvin.talkback',
}

def prepare():
    from PIL import Image
    PACK.mkdir(parents=True, exist_ok=True)
    atlas = Image.open(PACK / 'atlas.png').convert('RGBA')
    assert atlas.width == atlas.height, atlas.size
    assert atlas.getextrema()[3][0] < 255, 'Atlas must preserve transparency'
    icons = PACK / 'icons'
    icons.mkdir(exist_ok=True)
    # Generated atlas has slightly nonuniform row spacing; verified cut lines
    # are in transparent gutters. Never cut through a star or mascot.
    xs = [round(v * atlas.width / 1254) for v in (0,167,322,477,631,788,938,1097,1254)]
    ys = [round(v * atlas.height / 1254) for v in (0,179,346,508,665,822,965,1099,1254)]
    for i, name in enumerate(NAMES):
        x, y = i % 8, i // 8
        tile = atlas.crop((xs[x], ys[y], xs[x+1], ys[y+1]))
        tile = tile.crop(tile.getbbox())
        tile.thumbnail((164,164), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA',(192,192))
        canvas.paste(tile,((192-tile.width)//2,(192-tile.height)//2))
        canvas.save(icons / ('pastel_' + name + '.png'))
    preview = Image.new('RGB',(8*192,8*216),'#fff0f3')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(preview)
    for i,name in enumerate(NAMES):
        tile = Image.open(icons / ('pastel_'+name+'.png'))
        x,y = (i%8)*192,(i//8)*216
        preview.paste(tile,(x,y),tile)
        draw.text((x+12,y+194),name.replace('_',' '),fill='#884b60')
    preview.save(PACK/'preview.png')
    mapping = {p: name for name, packages in GROUPS.items() for p in packages.split()}
    installed = (WS / 'device-inspection/icon-pack-installed-packages.txt').read_text().splitlines()
    for line in installed:
        if line.startswith('package:'):
            mapping.setdefault(line[8:].strip(), 'generic')
    activities = []
    for line in (WS / 'device-inspection/icon-pack-launcher-activities.txt').read_text().splitlines():
        m = re.match(r'\s+([\w.]+)/([\w.]+)\s*$', line)
        if m:
            pkg, cls = m.groups()
            if cls.startswith('.'): cls = pkg + cls
            activities.append((pkg, cls))
    (PACK / 'packages.json').write_text(json.dumps(mapping, indent=2, sort_keys=True) + '\n')
    (PACK / 'packages.properties').write_text(''.join(p + '=' + n + '\n' for p,n in sorted(mapping.items())))
    xml = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for pkg, cls in activities:
        xml.append('  <item component="ComponentInfo{%s/%s}" drawable="pastel_%s" />' % (pkg, cls, mapping[pkg]))
    for pkg, name in sorted(mapping.items()):
        xml.append('  <item component="%s" drawable="pastel_%s" />' % (escape(pkg),name))
    xml.append('</resources>')
    (PACK / 'appfilter.xml').write_text('\n'.join(xml)+'\n')
    settings_icons = sorted((PACK/'settings-icons').glob('*.png'))
    coverage = {'icons': len(NAMES)+len(settings_icons), 'launcher_icons':len(NAMES), 'settings_icons':len(settings_icons), 'installed_packages': len(installed), 'launcher_activities': len(activities),
                'unmapped_launcher_activities': [p for p,c in activities if mapping[p]=='generic'],
                'scope': 'KYF37 Home launcher icons plus Settings menu extension; background services receive generic package mappings'}
    assert not coverage['unmapped_launcher_activities'], coverage
    (PACK / 'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    with zipfile.ZipFile(PACK / 'pastel-star-icon-pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(icons.glob('*.png')): z.write(p, 'res/drawable-nodpi/'+p.name)
        for p in settings_icons: z.write(p, 'res/drawable-nodpi/'+p.name)
        for name in ('appfilter.xml','packages.json','coverage.json','README.md','generation-prompt.txt','preview.png','settings-preview.png','settings-generation-prompt.txt','settings-coverage.json'):
            if (PACK/name).exists(): z.write(PACK/name,name)
    print(json.dumps(coverage))

def apply():
    assets = HOME / 'assets/pastel-star'
    assets.mkdir(parents=True, exist_ok=True)
    for p in (PACK/'icons').glob('*.png'): shutil.copy2(p, assets/p.name)
    shutil.copy2(PACK/'packages.properties', assets/'packages.properties')
    helper = WS / 'device-inspection/Kyf37PastelIcons.java.txt'
    shutil.copy2(helper, HOME / 'src/org/kyf37/home/PastelIcons.java')
    # Patch both current source and the template used by quick-keys rebuilds.
    for p in (HOME/'src/org/kyf37/home/Home.java', WS/'device-inspection/Kyf37Home.java.txt'):
        s = p.read_text()
        s = s.replace('t.icon = info.loadIcon(pm);', 't.icon = PastelIcons.get(this, info.activityInfo.packageName);')
        p.write_text(s)
    manifest = HOME/'AndroidManifest.xml'
    s = manifest.read_text()
    res = HOME/'res/drawable-nodpi'
    res.mkdir(parents=True,exist_ok=True)
    shutil.copy2(PACK/'icons/pastel_home.png',res/'pastel_home.png')
    if 'android:icon="@drawable/pastel_home"' not in s:
        s = s.replace('<application ', '<application android:icon="@drawable/pastel_home" ',1)
    manifest.write_text(s)
    print('Pastel Star installed in Kyf37Home source and quick-keys template')

if __name__ == '__main__':
    if '--prepare' in sys.argv: prepare()
    else: apply()
