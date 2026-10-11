# KYF37 Android 10 Go v18

Owner-specific release candidate for serial 981108631314. This version includes
the current Kyf37Home launcher without its large clock, larger themed icons,
Standard/Pastel Star/Sky Star appearance selection and wallpaper-aware text.
It includes the single-center-button Kyf37Flashlight, keypad notification and
quick-settings UI, larger lock clock, visible focus outlines, and native Kyocera
app softkeys. The generic SystemUI bottom bar is disabled.

Source integration also includes the current outer-display animation/video,
audio PCM compatibility, camera/JPEG compatibility, storage and JIT/kernel work.
The image must pass current boot, filesystem, module ABI, UI asset and vendor
symbol audits before packaging. Each new APK/framework asset is included in the
full image rather than applied as an isolated framework patch.

The 53 additional stock-app ports remain optional development candidates outside
the installed ROM. Static/signature checks do not prove their providers, services,
native ABI, audio routing, FeliCa transactions or carrier endpoints work. The
existing default dialer remains selected. Cellular registration, IMS/VoLTE,
FeliCa/NFC, One Seg TV and the remaining app API contracts are unfinished.

This candidate has not been flashed or hardware-boot-verified. Launcher APK
installation is tracked separately in current-home-install/installation.json.

Install through the existing physical-key TWRP only, with the microSD mounted at
/external_sd and at least 1.7 GB additional free space beyond the ZIP. The installer
checks device identity, partition geometry, payload/protected-partition hashes,
saves boot/system rollback copies, writes and fully verifies system and owner-signed
boot, and preserves userdata, recovery, owner keystore and modem. It never reboots
automatically. Keep verified stock rollback and the USB recovery runbook.

Rebuild using device-inspection/build-locked.sh with systemimage, then the existing
release packaging, validation, vendor audit, candidate staging, owner boot-signing
and TWRP ZIP builder. Never distribute the owner private signing key.
