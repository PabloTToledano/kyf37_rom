"""Save reviewed offline UI outputs only after both locked builds succeed."""
from pathlib import Path
import shutil,hashlib,json
here=Path(__file__).resolve().parent;workspace=here.parent
product=Path('/home/pablo/kyf37-android10/out/target/product/kyf37/system')
folder=workspace/'kyf37-rom/native-softkeys';folder.mkdir(exist_ok=True)
for name in ['native-only-bars-build.log','native-softkeys-final-build.log']:
 p=workspace/'kyf37-rom/keypad-focus'/name
 assert p.read_text(errors='replace').rstrip().endswith('BUILD_EXIT=0'),name
 shutil.copy2(p,folder/name)
files=[product/'framework/framework-res.apk',product/'framework/services.jar',product/'product/priv-app/SystemUI/SystemUI.apk',product/'priv-app/Kyf37Home/Kyf37Home.apk']
files += [product/'app'/module/(module+'.apk') for module in ['KyoceraCamera','MemoPad','MemoPadProvider','Reader','kc_soundrecorder','kc_soundrecorder_manager']]
records=[]
for source in files:
 assert source.is_file(),source
 target=folder/source.name;shutil.copy2(source,target)
 records.append({'file':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(folder/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in records))
(folder/'manifest.json').write_text(json.dumps({'artifacts':records,'hardware_verified':False,'installed':False,'full_rom_installer':False},indent=2)+'\n')
(folder/'README.md').write_text('''# Native-only app softkeys and launcher clock removal

Both locked builds passed. Native bridge/artwork release verification passed.
Source policy and reconstruction instructions: ../../NATIVE-SOFTKEYS.md.
These are OFFLINE build artifacts, not a ROM installer or hardware validation.
Do not install isolated framework/services jars: use matching validated ROM/ART
outputs and the normal owner-signed release/rollback pipeline. Current default
dialer remains unchanged; its experimental test APK is in ../stock-dialer-port/.
''')
print('Saved',len(records),'offline artifacts to',folder)
