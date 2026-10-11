"""Verify original APK preservation, launcher routing and bounded media design. No phone access."""
from pathlib import Path
import subprocess,zipfile,re,json
here=Path(__file__).resolve().parent;tree=Path('/home/pablo/kyf37-android10')
base=here.parent/'kyf37-rom/all-stock-app-ports/signed-apks/Kyf37StockDataFolder.apk'
port=tree/'packages/apps/Kyf37RemainingStockApps/Kyf37StockDataFolder.apk'
with zipfile.ZipFile(base) as original,zipfile.ZipFile(port) as modified:
    kept=[n for n in original.namelist() if n!='AndroidManifest.xml' and not n.startswith('META-INF/')]
    assert all(original.read(n)==modified.read(n) for n in kept)
    original_dex=[n for n in original.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
    new_dex=[n for n in modified.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
    assert len(new_dex)==len(original_dex)+1
    assert b'GalleryInstrumentation' not in modified.read(next(n for n in new_dex if n not in original_dex))
aapt=tree/'out/host/linux-x86/bin/aapt2'
manifest=subprocess.check_output([str(aapt),'dump','xmltree',str(port),'--file','AndroidManifest.xml'],text=True)
assert '"jp.kyocera.datafolder"' in manifest
assert '"org.kyf37.gallery.GalleryActivity"' in manifest
assert '"jp.kyocera.datafolder.activity.DataFolderActivity"' in manifest
assert '"jp.kyocera.player.app.GalleryAppImpl"' in manifest
assert '"Gallery"' in manifest
assert '"android.permission.READ_EXTERNAL_STORAGE"' in manifest
print('PASS:',len(kept),'original entries byte-identical; modern + legacy activities; original application; test code excluded')
