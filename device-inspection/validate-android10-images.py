"""Offline validation only. Never accesses a phone or private signing key."""
from pathlib import Path
import subprocess, json, struct, hashlib, argparse

parser=argparse.ArgumentParser()
parser.add_argument('--boot',type=Path,default=Path('/home/pablo/kyf37-rom/boot-android10-legacy-unsigned.img'))
parser.add_argument('--raw-output',type=Path,default=Path('/home/pablo/kyf37-rom/system-android10-validated.raw.img'))
args=parser.parse_args()

workspace=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
scripts=workspace/'device-inspection'
reports=workspace/'kyf37-rom'
tree=Path('/home/pablo/kyf37-android10')
product=tree/'out/target/product/kyf37'
def run(*args):
    subprocess.run([str(x) for x in args],check=True)
outer_apk=product/'system/priv-app/Kyf37OuterScreen/Kyf37OuterScreen.apk'
run('python3',scripts/'verify-outer-release-assets.py','--apk',outer_apk)
assert 'KYF37 legacy PCM config ABI' in (tree/'external/tinyalsa/pcm.c').read_text(), 'Stock audio ABI fix missing'
boot=args.boot
system=product/'system.img'
assert boot.is_file() and system.is_file(), 'Both completed images are required'
run('python3',scripts/'verify-rom-boot.py',boot,'--expected-kernel',tree/'device/kyocera/kyf37/kernel','--kernel-policy-max','30','--require-legacy-first-stage','--report',reports/'android10-boot-verification.json')
run('python3',scripts/'verify-rom-system-sparse.py',system,'--report',reports/'android10-system-sparse-verification.json')
run('python3',scripts/'verify-rom-ui-sounds.py','--tree',tree,'--report',reports/'android10-ui-sound-verification.json')
raw=args.raw_output
assert not raw.exists(), 'Refusing to overwrite a previous raw candidate'
run(tree/'out/host/linux-x86/bin/simg2img',system,raw)
assert raw.stat().st_size == 1612709888
check=subprocess.run(['e2fsck','-f','-n',str(raw)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(reports/'android10-e2fsck.txt').write_text(check.stdout)
assert check.returncode == 0, ('Read-only filesystem check failed',check.returncode)
features=subprocess.check_output(['dumpe2fs','-h',str(raw)],stderr=subprocess.STDOUT,text=True)
(reports/'android10-filesystem-header.txt').write_text(features)
# New policies must fit the kernel's verified binary policy maximum, regardless
# of the separate VINTF platform-policy release number.
policy_checks={}
for rel in ['vendor/etc/selinux/precompiled_sepolicy','etc/selinux/precompiled_sepolicy','etc/selinux/sepolicy']:
    target=Path('/home/pablo/kyf37-rom')/('android10-policy-'+rel.replace('/','-'))
    result=subprocess.run(['debugfs','-R','dump /'+rel+' '+str(target),str(raw)],capture_output=True,text=True)
    if target.exists():
        data=target.read_bytes()
        version=struct.unpack_from('<I',data,16)[0]
        assert 15 <= version <= 30, (rel,version)
        policy_checks[rel]={'binary_version':version,'sha256':hashlib.sha256(data).hexdigest()}
        target.unlink()
boot_check=json.loads((reports/'android10-boot-verification.json').read_text())
assert policy_checks or boot_check['ramdisk_policy_version'] is not None, 'No packaged binary SELinux policy verified'
image_assets={}
stock_sounds=Path('/home/pablo/kyf37-rom/stock-system/media/audio/ui')
staged_modules=tree/'vendor/kyocera/kyf37/proprietary/lib/modules'
assets=[('media/audio/ui/'+p.name,p) for p in stock_sounds.iterdir() if p.is_file()]
assets += [('lib/modules/'+str(p.relative_to(staged_modules)),p) for p in staged_modules.rglob('*.ko')]
assets += [('etc/apns-conf.xml',tree/'device/kyocera/kyf37/apns-conf.xml'),
           ('bin/kyf37_qmux',product/'system/bin/kyf37_qmux')]
assets += [('vendor/lib/hw/lights.kyf37.so',product/'system/vendor/lib/hw/lights.kyf37.so')]
assets += [('priv-app/Kyf37OuterScreen/Kyf37OuterScreen.apk',outer_apk),
           ('lib/libkyf37subdisplay.so',product/'system/lib/libkyf37subdisplay.so'),
           ('lib/libtinyalsa.so',product/'system/lib/libtinyalsa.so')]
# Keep the owner's launcher and native-only softkey policy in every release.
# Compare packaged files with the current build, catching stale installer inputs.
assets += [('framework/framework-res.apk',product/'system/framework/framework-res.apk'),
           ('product/priv-app/Settings/Settings.apk',product/'system/product/priv-app/Settings/Settings.apk'),
           ('product/priv-app/SystemUI/SystemUI.apk',product/'system/product/priv-app/SystemUI/SystemUI.apk'),
           ('priv-app/Kyf37Home/Kyf37Home.apk',product/'system/priv-app/Kyf37Home/Kyf37Home.apk'),
           ('app/Kyf37PhoneSettings/Kyf37PhoneSettings.apk',product/'system/app/Kyf37PhoneSettings/Kyf37PhoneSettings.apk'),
           ('app/Kyf37Flashlight/Kyf37Flashlight.apk',product/'system/app/Kyf37Flashlight/Kyf37Flashlight.apk')]
run('python3',scripts/'verify-native-softkey-assets.py','--tree',tree)
for module in ['KyoceraCamera','MemoPad','MemoPadProvider','Reader','kc_soundrecorder','kc_soundrecorder_manager']:
    assets.append(('app/'+module+'/'+module+'.apk',product/'system/app'/module/(module+'.apk')))
# Wi-Fi HIDL requires the STA overlay to prevent wlan0 being registered as P2P.
# Validate the image, not just the source copy rules (v15 omitted both files).
wifi_config = tree/'device/kyocera/kyf37/radio'
assert 'p2p_disabled=1' in (wifi_config/'wpa_supplicant_overlay.conf').read_text().splitlines()
assets += [('vendor/etc/wifi/'+name,wifi_config/name) for name in
           ['wpa_supplicant_overlay.conf','p2p_supplicant_overlay.conf']]
# v22: the live brightness and SIM/data fixes must also reach the packaged image.
assets += [('vendor/lib/libril.so', product/'system/vendor/lib/libril.so')]
assets += [('app/'+module+'/'+module+'.apk',product/'system/app'/module/(module+'.apk'))
           for module in ['Kyf37Dialer','Kyf37Messages','Kyf37Contacts']]
for rel,expected in assets:
    target=Path('/home/pablo/kyf37-rom')/'android10-image-asset.tmp'
    assert not target.exists()
    run('debugfs','-R','dump /'+rel+' '+str(target),raw)
    assert target.is_file(), ('Asset missing from image',rel)
    actual=hashlib.sha256(target.read_bytes()).hexdigest()
    want=hashlib.sha256(expected.read_bytes()).hexdigest()
    target.unlink()
    assert actual == want, ('Packaged asset mismatch',rel)
    image_assets[rel]=actual
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest()}
report={'boot':digest(boot),'sparse_system':digest(system),'raw_system':digest(raw),'policy_checks':policy_checks,'image_assets':image_assets,'filesystem_check_exit':check.returncode,'hardware_boot_verified':False,'owner_signed':False}
(reports/'android10-image-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
