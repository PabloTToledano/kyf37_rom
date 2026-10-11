"""Build the owner-specific TWRP ZIP from validated signed images."""
from pathlib import Path
import hashlib,json,zipfile,subprocess,sys,os
root=Path(__file__).resolve().parent.parent
V10_README = """# KYF37 Android 10 Go v10 installer

LineageOS 17.1 / AOSP Android 10 QQ3A.200805.001 (ARM32, low-RAM) for owner serial 981108631314. Release boot: authenticated root ADB stays available, but the 600-second return-to-TWRP timer, the next-boot recovery guard and cache debug logging of earlier development builds are NOT present.

New in v10: side key toggles the notification shade when the lid is open and the phone unlocked (closed-lid clock behaviour kept); opening the lid answers a ringing call; compact single-row soft-key legend (F1 / Pointer-D-pad / Select-Click / Menu / Home) replaces the two-row 64dp footer; the supplied Kirby 480x854 boot animation; original Kyocera Camera, Memo pad (+provider), Flashlight, Sound recorder and Barcode reader ported from the stock deodexed apps with their Kyocera shared libraries; scrcpy-compatible software OMX encoder configuration persisted in the image.

Install only through the existing physical-key TWRP 3.7.0_9-0 with /external_sd mounted and at least 1.7 GB free besides this ZIP. The installer verifies serial, partition geometry, payload hashes and protected partitions, backs up current boot/system to microSD, writes and fully reads back owner-signed boot and system, and preserves userdata, recovery, keystore and modem. It never reboots automatically.

v11 also adds: icon-grid home launcher (3 columns, D-pad focus, digits 1-9 open the first nine tiles), End key acts as Home outside calls, privapp allowlist for org.kyf37.keypad (v10 stalled at the boot screen without it), and a glFinish before client-target hand-off to remove GPU/panel tearing.

v12 adds the quick-launch keypad (see KEYPAD.md): Contacts/Camera/Mail/Apps keys, Apps+digit slots, Clear hold = Memo, Call hold = Bluetooth pairing, corrected legend; the old-app compatibility dialog is disabled so the original Camera and Flashlight start.

v13 uses the supplied 120-frame 30 fps Kirby boot animation (sha256 e6718957...adf).

v14 adds: microG (GmsCore/companion/GSF proxy) with signature spoofing; Wi-Fi supplicant service; camera fixes (Kyocera AE/AWB libs, Kyocera Camera API stubs, provider ordering); cpuset groups; Phone settings app; original Kyocera ringtones; default wallpaper; the user-supplied boot animation (sha256 fdaf4860...4106).

v15 adds the preinstalled Aurora Store 4.8.4.

v17 adds Movistar official boot sound effect (normalized 48kHz 16-bit stereo PCM) to the 120-frame Kirby boot animation and persist.sys.bootanim.play_sound=1.

Known limits: Wi-Fi firmware start fails on this hardware (status 38); camera sensor capture and IMS/VoLTE remain unverified.
"""
revision=sys.argv[1] if len(sys.argv)==2 else 'v2'
assert revision in ('v2','v3','v4','v5','v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v17','v18','v19','v20','v22','v23')
candidate=root/('kyf37-rom/android10-go-candidate-20261007'+('-'+revision if revision!='v2' else ''))
output=root/('kyf37-rom/kyf37-android10-go-20261007-twrp-'+revision+'.zip')
if revision=='v23':
    output=root/'kyf37-rom/kyf37-android10-go-20261007-twrp-v23-keypad.zip'
assert not output.exists()
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
images={'boot.img':(candidate/'boot-android10-owner-signed.img',16777216,'97606038d0450d02c15013b93aa34adece314b956e84e94b04eb2e0ec2533b45'),
        'system.raw.img':(candidate/'system-android10.raw.img',1612709888,'155feaec297bf2053415bcc39ff3858c1ec01b98857a10dba8de20e5670540a5')}
if revision=='v3':
    images={'boot.img':(candidate/'boot-android10-owner-signed.img',16777216,'cd5e3b00e83b404a321b19650c7d0c458577b6a141d657a4097139b873c36f2f'),
            'system.raw.img':(candidate/'system-android10.raw.img',1612709888,'1ba81642db8719c823e6f9a77aa87faf2f6358f3f1c04bb43f4da79131dc6cff')}
if revision in ('v4','v5','v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v17','v18','v19','v20','v22','v23'):
    signing=json.loads((candidate/'boot-android10-owner-signed.signing.json').read_text())
    validation=json.loads((candidate/'android10-image-validation.json').read_text())
    assert signing['signature_verified'] and signing['body_preserved']
    assert validation['filesystem_check_exit']==0
    modules=json.loads((candidate/'android10-kernel-module-audit.json').read_text())['modules']
    assert len(modules)==15
    assert all(not m['missing_exports'] and not m['crc_mismatches'] and
               m['unsupported_loaded_relocations']==[] for m in modules)
    images={'boot.img':(candidate/'boot-android10-owner-signed.img',16777216,signing['sha256']),
            'system.raw.img':(candidate/'system-android10.raw.img',1612709888,validation['raw_system']['sha256'])}
if revision in ('v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v17','v18','v19','v20','v22','v23'):
    actual=json.loads((candidate/'android10-installed-vendor-symbol-audit.json').read_text())
    assert len(actual['files'])==(193 if revision in ('v18','v19','v20','v22','v23') else 180 if revision in ('v17','v20') else 177 if revision in ('v14','v15') else 175 if revision in ('v10','v11','v12','v13') else 173 if revision=='v9' else 160 if revision=='v8' else 159)
    assert not any(f['missing_libraries'] or f['unresolved_strong_symbols'] for f in actual['files'])
for path,size,digest in images.values():assert path.stat().st_size==size and sha(path)==digest
if revision in ('v22','v23'):
    theme=json.loads((root/('kyf37-rom/'+revision+'-theme-validation.json')).read_text())
    assert theme['passed'] and theme['classic_icons']==80
    assert all(validation['image_assets'][name]==digest for name,digest in theme['asset_hashes'].items())
helpers={name:root/'device-inspection'/name for name in ['clear-system-temp-wp','clear-recovery-boot-temp-wp']}
for path in helpers.values():
    blob=path.read_bytes();assert blob[:5]==b'\x7fELF\x01' and int.from_bytes(blob[18:20],'little')==40
script=(root/'device-inspection/twrp-android10-update-binary.sh').read_text()
if revision=='v23': # v23 installed display-fixed recovery
    script=script.replace('RECOVERY_HASH=9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e', 'RECOVERY_HASH=c7f5a41565595607a10930ddb174f9755568c01156a6440c34abdb5cca25141d')
for variable,name in [('BOOT_HASH','boot.img'),('SYSTEM_HASH','system.raw.img')]:
    line=next(line for line in script.splitlines() if line.startswith(variable+'='))
    script=script.replace(line,variable+'='+images[name][2],1)
script=script.replace('@SYSTEM_WP_SHA@',sha(helpers['clear-system-temp-wp'])).replace('@BOOT_WP_SHA@',sha(helpers['clear-recovery-boot-temp-wp']))
assert '@SYSTEM_WP_SHA@' not in script and '@BOOT_WP_SHA@' not in script
generated=root/'kyf37-rom/android10-twrp-update-binary.sh'
generated.write_text(script,newline='\n')
if os.name=='nt':
    posix=generated.as_posix()
    assert len(posix)>3 and posix[1:3]==':/'
    wsl_path='/mnt/'+posix[0].lower()+posix[2:]
    subprocess.run(['wsl','-d','Ubuntu','--','sh','-n',wsl_path],check=True)
else:
    subprocess.run(['sh','-n',str(generated)],check=True)
tests=json.loads((root/'kyf37-rom/android10-twrp-installer-tests.json').read_text())
assert all(v=='passed' for v in tests['tests'].values())
readme='''# KYF37 Android 10 Go TWRP installer

This is the installer ZIP for the experimental LineageOS 17.1 / Android 10 Go candidate, specific to KYF37 serial 981108631314 and its enrolled owner signing keystore. It has passed offline image/signature checks and host installer tests; no Android 10 hardware boot has been verified. IMS/VoLTE service port remains incomplete.

Installation:
1. Copy kyf37-android10-go-20261007-twrp-v2.zip to the phone's microSD. Version 2 corrects the boot start-sector check to the live verified value 151552; the previous ZIP stopped before partition writes. Keep the verified stock backups and USB recovery runbook accessible.
2. Boot the already installed, verified physical-key TWRP 3.7.0_9-0. Mount the microSD at /external_sd. Allow at least 1.7 GB additional free space for rollback images, besides the ZIP.
3. In TWRP, choose Install, select this ZIP, and confirm using the recovery's physical-key controls. ZIP signature verification must be off for this unsigned installer ZIP. The boot image inside IS owner-signed and verified separately.
4. Wait for completion and readback verification. The installer saves current boot/system images plus hashes in /external_sd/KYF37-Android10-rollback-<timestamp>-<pid>. It preserves userdata, recovery, keystore, and modem contents. It does not format userdata, install another recovery, or reboot automatically.
5. Keep the rollback directory. Reboot only when ready for the first hardware boot test and log collection. Existing Android 5 userdata compatibility has not been established; a separately backed-up clean-data test may be needed later.

If installation fails, remain in TWRP and keep the error/recovery log. Do not reboot a partly installed system. Use the verified stock restoration procedure or restore both saved boot.img and system.img with their checksums; these raw rollback files are not a normal TWRP-format backup directory.

The installer validates device/serial, exact boot/system block paths, sizes and start sectors, exact recovery and owner-keystore hashes, and complete payload hashes before writes. It unmounts system and checks for other boot/system mounts. It clears only temporary eMMC write protection using the previously used KYF37 helpers. Protection groups overlap recovery, but recovery contents are not written; hashes are checked afterward. It writes system first, verifies it, then writes signed boot and verifies it. Failure can leave a mixed system/boot state; rollback images are created before either write.

Physical keypad navigation, original sound files, the secondary-screen service, Spanish APN/IMS profiles and the manual LTE preference utility are included. Hardware operation and current LTE mask after stock restoration remain unverified. APN profiles do not establish VoLTE or create missing RF hardware. No modem writes occur during installation.

Optional preflight from root TWRP ADB: extract META-INF/com/google/android/update-binary to /tmp/kyf37-preflight.sh, then run:
/sbin/sh /tmp/kyf37-preflight.sh 3 1 /external_sd/kyf37-android10-go-20261007-twrp-v2.zip --check-only
Check-only validates payload/device/storage without backups, unmounting, clearing protection or flashing.

TWRP updater interface reference: https://github.com/TeamWin/Team-Win-Recovery-Project/blob/android-9.0/install.cpp
'''
(root/'kyf37-rom/ANDROID10-TWRP-INSTALL.md').write_text(readme)
if revision=='v3':
    readme=readme.replace('-twrp-v2.zip','-twrp-v3.zip').replace('Version 2 corrects the boot start-sector check to the live verified value 151552; the previous ZIP stopped before partition writes.',
        'Version 3 includes the live-verified boot sector correction, restores legacy bootdevice partition links in Android 10 first/second-stage init, and sets early init fatal failures to request recovery. The owner reports version 2 bootlooped; this revised hardware boot is not yet verified.')
    if revision=='v8':
        readme = """# KYF37 Android 10 Go v8 development installer

Owner-specific LineageOS 17.1 / AOSP Android 10 (QQ3A.200805.001), ARM32 low-RAM build for KYF37 serial 981108631314. The preceding v7 reached Android setup and sys.boot_completed=1 with authenticated root ADB. This new revision requires hardware verification and remains a permissive development build.

Changes: F3 toggles the pointer globally; disabled mode preserves D-pad controls. F4 opens Home outside the original launcher. Physical keys wake with the lid open; Select/Enter opens the normal lock-screen bouncer without bypassing credentials. The exterior CAMERA side key lights the outer clock for ten seconds with the lid closed. SystemUI uses the original Kyocera footer artwork, two-row geometry and font size, with labels for the new global key actions. Original per-app softkey-label ABI is not restored.

The omitted original vm_bms fuel-gauge daemon is restored with a separate startup domain. Its bounded live test corrected the battery reading from 1% to 56%, matching Android Battery Service. Bluetooth device rules use valid named groups, and KYF37 startup deadlines allow the original five-second transport startup. Complete Bluetooth operation, keypad wake/unlock, pointer operation and outer-side-button behavior require tests on this revision.

Install the ZIP through the existing physical-key TWRP, with /external_sd mounted and at least 1.7 GB free in addition to the ZIP. The installer verifies serial, partition geometry, owner signature, payload hashes and protected partition hashes. It saves the current boot/system images on microSD before writing, writes and fully verifies system and signed boot, preserves userdata/recovery/keystore/modem, and does not reboot automatically. Wait for installation success before rebooting. Keep the saved rollback directory and verified stock backups.

This diagnostic boot saves cache logs and requests TWRP on the next restart. It automatically returns to TWRP after 600 seconds; this timer is for development testing. A stable daily-use release is not established. Shared-storage sdcardfs/esdfs support, old RIL Binder ABI and IMS/VoLTE remain unresolved. Spanish APN profiles and the manual LTE preference utility do not prove radio or additional-band operation. The installer performs no modem writes.
"""
    (root/'kyf37-rom/ANDROID10-TWRP-INSTALL.md').write_text(readme)
if revision in ('v4','v5','v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23'):
    readme=readme.replace('-twrp-v2.zip','-twrp-'+revision+'.zip').replace('Version 2 corrects the boot start-sector check to the live verified value 151552; the previous ZIP stopped before partition writes.',
        'Version 4 uses the source-recommended GCC 4.8 kernel, which has booted TWRP successfully in a kernel-only hardware test. The otherwise identical GCC 4.9 kernel failed. Matching modules and legacy partition-link fixes are included. Android userspace boot remains unverified.')
    if revision=='v5':
        readme += '\nVersion 5 adds real ARM mmap entropy controls and ambient-capability support required by Android 10. Both interfaces passed hardware tests in TWRP with this kernel; all 15 rebuilt modules passed export, CRC and loaded-relocation checks. Android userspace remains under test.\n'
    if revision in ('v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23'):
        readme += '\nVersion 6 corrects duplicate CAS declarations in the hardware manifest, installs matching CAF display providers in the default linker namespace, defers Kyocera SoundPool initialization until after boot, and declares the firmware mount label. Interpreter/AOT mode avoids the missing memfd_create JIT interface. This diagnostic trial returns to recovery after 120 seconds and saves Android logs. Hardware boot completion is still under test.\n'
    if revision in ('v7','v8','v9','v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23'):
        readme=readme.replace('after 120 seconds','after 600 seconds')
        readme += '\nVersion 7 restores all 30 original remote-filesystem links required by the Qualcomm modem TFTP service. Their hardware test removed the immediate modem-triggered kernel panic and reached Android setup, reported by the owner. It sets the USB serial before enabling the OEM gadget and uses synchronous FunctionFS for Linux 3.10. The Bluetooth HAL reads the existing nine-byte Qualcomm factory NV record without changing it. These Bluetooth/ADB changes remain under hardware test. Shared-storage filesystem support and radio ABI failures are unresolved; this remains a development trial, not a daily-use release.\n'
    readme += '\nDevelopment diagnostic trial: the ramdisk marker enables cache logging at /cache/kyf37-init.log through an auxiliary cache mount. During init it sets only the misc command to boot-recovery, preserving remaining bytes, so the following restart enters existing TWRP. Clear this temporary guard only after a successful Android boot test. No data formatting or automatic modem writes occur.\n'
    if revision=='v8':
        readme = """# KYF37 Android 10 Go v8 development installer

Owner-specific LineageOS 17.1 / AOSP Android 10 (QQ3A.200805.001), ARM32 low-RAM build for KYF37 serial 981108631314. The preceding v7 reached Android setup and sys.boot_completed=1 with authenticated root ADB. This new revision requires hardware verification and remains a permissive development build.

Changes: F3 toggles the pointer globally; disabled mode preserves D-pad controls. F4 opens Home outside the original launcher. Physical keys wake with the lid open; Select/Enter opens the normal lock-screen bouncer without bypassing credentials. The exterior CAMERA side key lights the outer clock for ten seconds with the lid closed. SystemUI uses the original Kyocera footer artwork, two-row geometry and font size, with labels for the new global key actions. Original per-app softkey-label ABI is not restored.

The omitted original vm_bms fuel-gauge daemon is restored with a separate startup domain. Its bounded live test corrected the battery reading from 1% to 56%, matching Android Battery Service. Bluetooth device rules use valid named groups, and KYF37 startup deadlines allow the original five-second transport startup. Complete Bluetooth operation, keypad wake/unlock, pointer operation and outer-side-button behavior require tests on this revision.

Install the ZIP through the existing physical-key TWRP, with /external_sd mounted and at least 1.7 GB free in addition to the ZIP. The installer verifies serial, partition geometry, owner signature, payload hashes and protected partition hashes. It saves the current boot/system images on microSD before writing, writes and fully verifies system and signed boot, preserves userdata/recovery/keystore/modem, and does not reboot automatically. Wait for installation success before rebooting. Keep the saved rollback directory and verified stock backups.

This diagnostic boot saves cache logs and requests TWRP on the next restart. It automatically returns to TWRP after 600 seconds; this timer is for development testing. A stable daily-use release is not established. Shared-storage sdcardfs/esdfs support, old RIL Binder ABI and IMS/VoLTE remain unresolved. Spanish APN profiles and the manual LTE preference utility do not prove radio or additional-band operation. The installer performs no modem writes.
"""
    (root/'kyf37-rom/ANDROID10-TWRP-INSTALL.md').write_text(readme)
if revision in ('v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23'):
    readme = V10_README.replace('v10',revision)
if revision=='v9':
    readme = """# KYF37 Android 10 Go v9 development installer

LineageOS 17.1 / AOSP Android 10 QQ3A.200805.001, ARM32 low-RAM build for owner serial 981108631314.

Includes physical F3/scancode65 pointer mapping, configurable keypad settings, Hangup no-sleep policy, visible original-artwork footer, closed-lid clock, TT9 full v64.0 as initial default, original infrared APK port/native daemon/UART arbitration, Camera2 and restored OV8856 sensor/tuning/EEPROM/actuator files. Includes the owner-supplied ICOCA/Kirby bootanimation ZIP: 480x854, 16 frames, 12fps looping.

Scrcpy legacy software H264 encoding recorded valid 480x854 video in a live test. Codec2 is disabled for this hardware because its HIDL graphics mapper is unavailable; original software OMX codecs and complete XML configuration are supplied. Laptop launcher: tools/scrcpy/Start-KYF37.ps1 in the workspace.

V8 hardware testing reached Bluetooth ON and one rear camera after sensor/Binder corrections, but camera orientation/preview/capture and actual infrared transfer still require validation. TT9 installed and selected successfully; predictive keypad typing remains to be tested. All v9 integrated behavior is unverified until this package boots.

V8 subsequently panicked in sched_get_nr_running_avg iowait accounting. V9 GCC4.8 kernel fixes sampling under the per-CPU lock, 64-bit nanosecond/counter arithmetic and accumulation across CPUs, preserving diagnostic BUG checks. All 15 matching modules passed exports/CRCs/loaded-relocation audit; long hardware stability remains unverified.

Install only through existing physical-key TWRP with /external_sd mounted and at least 1.7GB additional free space besides this ZIP. Installer backs up current boot/system, checks payload/protected partition hashes and partition geometry, writes and fully verifies system and owner-signed boot, preserves userdata/recovery/owner keystore/modem and never reboots automatically. Keep verified stock rollback.

Development boot uses authenticated root ADB, AOT/interpreter, permissive policy, cache diagnostics, next-reboot TWRP guard and 600-second return timer. Radio Binder ABI, IMS/VoLTE and shared-storage filesystem support remain unresolved. APNs or LTE preference utilities do not establish radio/band functionality. No modem writes are performed.
"""
    (root/'kyf37-rom/ANDROID10-TWRP-INSTALL.md').write_text(readme)

if revision in ('v18','v19','v20','v22','v23'):
    readme=(root/('kyf37-rom/RELEASE-%s.md' % revision)).read_text()
    (root/'kyf37-rom/ANDROID10-TWRP-INSTALL.md').write_text(readme)

temporary=output.with_suffix('.zip.partial');assert not temporary.exists()
manifest={}
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    def addtext(name,data,executable=False):
        info=zipfile.ZipInfo(name,(2026,10,7,12,0,0));info.create_system=3
        info.external_attr=(0o100755 if executable else 0o100644)<<16
        info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
    addtext('META-INF/com/google/android/update-binary',script,True)
    addtext('META-INF/com/google/android/updater-script','# Installation is performed by the checked shell update-binary.\n')
    addtext('README.md',readme)
    if revision in ('v22','v23'):
        z.write(root/('kyf37-rom/'+revision+'-theme-validation.json'),'reports/'+revision+'-theme-validation.json')
    for name,(path,size,digest) in images.items():
        z.write(path,name);manifest[name]={'bytes':size,'sha256':digest}
    for name,path in helpers.items():
        z.write(path,'tools/'+name);manifest['tools/'+name]={'bytes':path.stat().st_size,'sha256':sha(path)}
    addtext('payload-manifest.json',json.dumps(manifest,indent=2)+'\n')
    for name in ['android10-image-validation.json','android10-spain-carriers.json','android10-twrp-installer-tests.json']+(['android10-legacy-block-links.json'] if revision in ('v3','v4','v5','v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23') else []):
        z.write(root/'kyf37-rom'/name,'reports/'+name)
    if revision in ('v4','v5','v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23'):
        for name in ['android10-kernel-module-audit.json','android10-gcc48-correction.json']:
            z.write(root/'kyf37-rom'/name,'reports/'+name)
    if revision in ('v6','v7','v8','v9','v10','v11','v12','v13','v14','v15','v18','v19','v20','v22','v23'):
        z.write(candidate/'android10-installed-vendor-symbol-audit.json','reports/android10-installed-vendor-symbol-audit.json')
    z.write(candidate/'BoringSSL-LICENSE.txt','BoringSSL-LICENSE.txt')
    z.write(root/'KYF37-PROJECT.md','KYF37-PROJECT.md')
    for name in ['clear_system_temp_wp.c','clear_recovery_boot_temp_wp.c','read_emmc_wp.c']:
        z.write(root/'device-inspection'/name,'tools/source/'+name)
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
    for name,record in manifest.items():
        h=hashlib.sha256()
        with z.open(name) as f:
            for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
        assert h.hexdigest()==record['sha256'] and z.getinfo(name).file_size==record['bytes']
    assert z.read('META-INF/com/google/android/update-binary')==script.encode()
    assert not any('private' in n or 'owner-signing-key' in n for n in z.namelist())
temporary.rename(output)
report={'revision':revision,'zip':str(output),'bytes':output.stat().st_size,'sha256':sha(output),
        'zip_crc_and_payload_hashes_verified':True,'installer_tests':tests,
        'phone_accessed':False,'hardware_installation_tested':False,'hardware_boot_verified':False,
        'backup_required':True,'automatic_reboot':False,'userdata_wipe':False}
(root/'kyf37-rom/android10-twrp-installer.json').write_text(json.dumps(report,indent=2)+'\n')
(root/('kyf37-rom/'+revision+'-validation.json')).write_text(json.dumps(report,indent=2)+'\n')
output.with_suffix('.zip.sha256').write_text(report['sha256']+'  '+output.name+'\n')
print(json.dumps(report,indent=2))

