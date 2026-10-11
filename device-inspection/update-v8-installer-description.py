from pathlib import Path
p=Path('device-inspection/build-twrp-android10-installer.py')
s=p.read_text()
a="    (root/'kyf37-rom/ANDROID10-TWRP-INSTALL.md').write_text(readme)"
b='''    if revision=='v8':
        readme = """# KYF37 Android 10 Go v8 development installer

Owner-specific LineageOS 17.1 / AOSP Android 10 (QQ3A.200805.001), ARM32 low-RAM build for KYF37 serial 981108631314. The preceding v7 reached Android setup and sys.boot_completed=1 with authenticated root ADB. This new revision requires hardware verification and remains a permissive development build.

Changes: F3 toggles the pointer globally; disabled mode preserves D-pad controls. F4 opens Home outside the original launcher. Physical keys wake with the lid open; Select/Enter opens the normal lock-screen bouncer without bypassing credentials. The exterior CAMERA side key lights the outer clock for ten seconds with the lid closed. SystemUI uses the original Kyocera footer artwork, two-row geometry and font size, with labels for the new global key actions. Original per-app softkey-label ABI is not restored.

The omitted original vm_bms fuel-gauge daemon is restored with a separate startup domain. Its bounded live test corrected the battery reading from 1% to 56%, matching Android Battery Service. Bluetooth device rules use valid named groups, and KYF37 startup deadlines allow the original five-second transport startup. Complete Bluetooth operation, keypad wake/unlock, pointer operation and outer-side-button behavior require tests on this revision.

Install the ZIP through the existing physical-key TWRP, with /external_sd mounted and at least 1.7 GB free in addition to the ZIP. The installer verifies serial, partition geometry, owner signature, payload hashes and protected partition hashes. It saves the current boot/system images on microSD before writing, writes and fully verifies system and signed boot, preserves userdata/recovery/keystore/modem, and does not reboot automatically. Wait for installation success before rebooting. Keep the saved rollback directory and verified stock backups.

This diagnostic boot saves cache logs and requests TWRP on the next restart. It automatically returns to TWRP after 600 seconds; this timer is for development testing. A stable daily-use release is not established. Shared-storage sdcardfs/esdfs support, old RIL Binder ABI and IMS/VoLTE remain unresolved. Spanish APN profiles and the manual LTE preference utility do not prove radio or additional-band operation. The installer performs no modem writes.
"""
'''
assert a in s
s=s.replace(a,b+a)
p.write_text(s)
