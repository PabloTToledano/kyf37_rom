"""Verify theme/wallpaper against actual final build APKs, not earlier live copies."""
from pathlib import Path
import io, json, zipfile, hashlib, sys
from PIL import Image
root = Path(__file__).resolve().parent.parent
revision = sys.argv[1] if len(sys.argv)>1 else 'v22'
assert revision in ('v22','v23')
art = root/'kyf37-rom/kyocera-classic'
product = Path('//wsl.localhost/Ubuntu/home/pablo/kyf37-android10/out/target/product/kyf37/system')
expected = Image.open(art/'wallpaper.png').convert('RGB')
def same(data):
    im = Image.open(io.BytesIO(data)).convert('RGB')
    return im.size == expected.size and im.tobytes() == expected.tobytes()
with zipfile.ZipFile(product/'priv-app/Kyf37Home/Kyf37Home.apk') as z:
    assert same(z.read('assets/owner-wallpaper.png'))
    icons = list((art/'icons').glob('classic_*.png'))
    assert len(icons) == 80
    for p in icons: assert z.read('assets/kyocera-classic/'+p.name) == p.read_bytes()
for rel in ('product/priv-app/Settings/Settings.apk', 'app/Kyf37PhoneSettings/Kyf37PhoneSettings.apk'):
    with zipfile.ZipFile(product/rel) as z:
        assert len([n for n in z.namelist() if '/classic_' in n and n.endswith('.png')]) == 80
with zipfile.ZipFile(product/'framework/framework-res.apk') as z:
    entries = [n for n in z.namelist() if n.endswith('/default_wallpaper.png') and 'sw600' not in n and 'sw720' not in n]
    assert entries and all(same(z.read(n)) for n in entries), entries
paths = ['priv-app/Kyf37Home/Kyf37Home.apk','product/priv-app/Settings/Settings.apk',
         'app/Kyf37PhoneSettings/Kyf37PhoneSettings.apk','framework/framework-res.apk']
report = {'passed':True, 'classic_icons':80, 'settings_icon_counts':[80,80], 'handset_wallpaper_entries':entries, 'source':'final '+revision+' build APKs', 'hardware_verified':False,
          'asset_hashes':{p:hashlib.sha256((product/p).read_bytes()).hexdigest() for p in paths}}
(root/('kyf37-rom/'+revision+'-theme-validation.json')).write_text(json.dumps(report, indent=2))
print(json.dumps(report))
