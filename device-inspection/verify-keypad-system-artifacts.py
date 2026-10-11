"""Read-only checks of compiled UI contracts; report does not imply hardware QA."""
from pathlib import Path
import hashlib
import json
import zipfile
import sys
root = Path('/home/pablo/kyf37-android10/out/target/product/kyf37/system')
here = Path(__file__).resolve().parent
checks = [('framework.jar', b'Kyf37SystemKeyGuide'),
          ('services.jar', b'Kyf37Navigation'),
          ('SystemUI.apk', b'Kyf37KeitaiGuide')]
for name in ['KyoceraCamera','MemoPad','Reader','kc_soundrecorder','kc_soundrecorder_manager']:
    checks.append((name+'.apk',b'keyIcon'))
for name in ['Kyf37Dialer','Kyf37Messages','Kyf37Contacts']:
    checks.append((name+'.apk',b'kyf37-corner-guide-v2'))
ports = Path('/home/pablo/kyf37-android10/packages/apps/Kyf37RemainingStockApps')
for apk in sorted(ports.glob('*.apk')):
    if list(root.rglob(apk.name)):
        with zipfile.ZipFile(apk) as z:
            if 'classes2.dex' in z.namelist() and b'Kyf37SoftkeyBridge' in z.read('classes2.dex'):
                checks.append((apk.name,b'keyIcon'))
report = {'hardware_verified':False,'installed_on_phone':False,
          'release_packaged':False,'owner_boot_signature_validated':False,
          'ready_to_flash':False,'artifacts':[]}
for name,contract in checks:
    matches = list(root.rglob(name))
    assert len(matches)==1,(name,matches)
    p = matches[0]
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None,p
        dex = [z.read(n) for n in z.namelist() if n.endswith('.dex')]
        assert any(contract in data for data in dex),(name,contract)
        if name=='SystemUI.apk':
            assert any(b'Contacts Dismiss' in data for data in dex),'Stale shade guide'
        if name=='framework.jar':
            assert any(b'kyf37-native-softkeys/package.txt' in data for data in dex),'Stale native-guide detection'
        if name=='services.jar':
            assert any(b'isPendingSoftkey' in data for data in dex),'Stale global quick-key routing'
    report['artifacts'].append({'path':str(p),'bytes':p.stat().st_size,
                               'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                               'dex_contract':contract.decode()})
log = Path(sys.argv[1] if len(sys.argv)>1 else '/home/pablo/keypad-system-polish-staged-final3.log')
assert log.read_text().rstrip().endswith('BUILD_EXIT=0'), 'Final build did not pass'
report['build_log']=str(log)
report['build_exit']=0
report['images']=[]
for name in ['boot.img','system.img']:
    p=root.parent/name
    assert p.is_file() and p.stat().st_size>0,p
    report['images'].append({'path':str(p),'bytes':p.stat().st_size})
dest = here/'keypad-ui-validation'
(dest/'host-validation.json').write_text(json.dumps(report,indent=2)+'\n')
(dest/'build-final.log').write_bytes(log.read_bytes())
print('KEYPAD_SYSTEM_ARTIFACTS_OK: framework, policy, SystemUI and installed native ports; NOT flashed')
