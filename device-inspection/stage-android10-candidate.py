"""Copy only offline-validated outputs into the Windows review folder."""
from pathlib import Path
import json, hashlib, shutil, sys
workspace=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
reports=workspace/'kyf37-rom'
validation=json.loads((reports/'android10-image-validation.json').read_text())
assert validation['filesystem_check_exit']==0
audit=json.loads((reports/'android10-vendor-symbol-audit.json').read_text())
assert len(audit['files'])==151
assert not any(f['missing_libraries'] or f['unresolved_strong_symbols'] for f in audit['files'])
folder_name=sys.argv[1] if len(sys.argv)==2 else 'android10-go-candidate-20261007'
assert Path(folder_name).name==folder_name and folder_name.startswith('android10-go-candidate-')
folder=reports/folder_name
folder.mkdir(exist_ok=True)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
for field,name in [('boot','boot-android10-unsigned.img'),('sparse_system','system-android10.sparse.img'),('raw_system','system-android10.raw.img')]:
    record=validation[field];source=Path(record['path'])
    assert source.stat().st_size==record['bytes'] and digest(source)==record['sha256']
    if (folder/name).exists():
        assert digest(folder/name)==record['sha256'], 'Existing staged image differs'
        continue
    temp=folder/(name+'.copying');shutil.copyfile(source,temp)
    assert digest(temp)==record['sha256']
    temp.rename(folder/name)
for name in ['android10-image-validation.json','android10-boot-verification.json','android10-system-sparse-verification.json','android10-vendor-symbol-audit.json','android10-e2fsck.txt','android10-filesystem-header.txt','android10-init-compat.json','android10-crypto-compat-tests.json','android10-kernel-module-audit.json','android10-spain-carriers.json','apns-conf-spain.xml']:
    shutil.copy2(reports/name,folder/name)
shutil.copy2('/home/pablo/kyf37-android10/external/boringssl/src/LICENSE',folder/'BoringSSL-LICENSE.txt')
(folder/'README.md').write_text('''# KYF37 Android 10 Go development candidate

Android 10, based on LineageOS 17.1 / AOSP QQ3A.200805.001, configured for low RAM and ARM32 Cortex-A7. This is an experimental userdebug build with permissive SELinux. It has not been boot-tested on the phone; a working daily-use ROM is not yet established.

Implemented in the build: physical D-pad/key navigation, multi-tap keypad input, F2 Menu / F3 Home / F4 pointer controls, a home-screen key guide, original Kyocera opening/closing/button recordings, and an outer-screen clock/battery service. Their operation on hardware remains unverified. Other closed-source Kyocera features are not fully ported. Select KYF37 Home if Android presents a home-app chooser.

Offline checks: exact rebuilt kernel and OEM device trees, full legacy ramdisk and early system mount, binary SELinux policy version, all 15 kernel-module export/CRC checks, dependency/strong-symbol closure for 151 stock ELF files, image geometry, read-only filesystem check, and on-image sound/module hashes. Symbol checks do not establish object-layout, ioctl or runtime compatibility.

The default build-tree boot.img has an unsuitable minimal ramdisk. Use only the separately packaged owner-signed boot candidate after its signing report is present. The unsigned image is for inspection. system-android10.raw.img is the expanded system image; system-android10.sparse.img is its Android sparse representation.

Spanish internet/MMS defaults are included for Movistar, Orange, DIGI and Vodafone, with dedicated IMS APN profiles. Orange/Movistar IMS profiles are experimental. The Android 5 Qualcomm IMS service has not been ported to Android 10; VoLTE/VoWiFi registration is not established by these APNs. DIGI documents that data roaming must be enabled; the ROM does not silently enable roaming for every SIM. Carrier sources and exact settings are in android10-spain-carriers.json.

Saved QMI readbacks show a previously applied LTE preference mask 0x0a0800c5 (bands 1,3,7,8,20,26,28), including a read after reboot. The current mask after stock restoration and actual RF reception remain unverified. The ROM contains /system/bin/kyf37_qmux: run through root ADB with no argument to read; --enable-spain explicitly applies the same additions only if the original known mask is present, or performs no write if the desired mask is already present. No automatic radio writes run at boot. A preference cannot create missing RF hardware or modem calibration. Preserve modem partitions and read the live mask before any further radio work.

No phone was flashed during this build. Recovery and modem/NV contents were not changed. App-managed root such as Magisk is not installed; the build supports development ADB root.

The image bundle is an archive of images and reports, not an automatic TWRP install ZIP. First hardware testing must use the known recovery/stock-restoration path documented in KYF37-USB-RECOVERY-RUNBOOK.md and verify the phone's live partition layout and enrolled owner keystore. Do not erase userdata as part of an automated test. Existing Android 5 userdata has not been tested with Android 10.

This product includes cryptographic software written by Eric Young (eay@cryptsoft.com). See BoringSSL-LICENSE.txt and Android's included notices.
''')
print(str(folder))
