# KYF37 Android 10 Go v22 — 2026-10-11

Owner-specific installer for KYF37 serial 981108631314. Android 10 / LineageOS 17.1, vendor kernel #17. Full current documentation and verified recovery procedure are included as KYF37-PROJECT.md.

Includes Kyocera Classic as the fourth Appearance choice, the supplied sky/castle default wallpaper, persistent launcher folders with corrected focus return, readable folder titles, an explicit Camera2 shortcut, Pixel-style native lock clock, current D-pad Settings/SystemUI controls, brightness vendor HAL, current stock-app ports and native keypad apps, outer-display animations/wide Bad Apple/audio compatibility, and both SIM-status and mobile-data libril fixes.

Prior live component checks established brightness-node changes, themes/folders, camera JPEG capture, outer-screen playback and Movistar GPRS. Those checks do not establish that this integrated v22 image has booted. v22 is host-validated; hardware installation/boot is pending. LTE, calls/SMS/IMS, video recording, full folder editing and physical-panel tearing remain open or incompletely tested. Android 10 has Material-inspired styling, not Android 12 Monet.

Install only through the existing physical-key TWRP with at least 1.7 GB additional SD space beyond this ZIP. The installer saves current boot/system, verifies geometry and protected partitions, writes and reads back system plus owner-signed release boot, preserves userdata/recovery/keystore/modem and never reboots automatically. Keep stock and SD rollback backups. If installation fails, stay in TWRP and restore both matching images before rebooting. This release has no diagnostic recovery timer/guard.

Existing wallpaper, folder and theme preferences are preserved; the default wallpaper applies to new/default selections. See the project guide for build commands, source scripts, evidence and recovery.

The v22 gate caught the old MobileLight prebuilt being reinstalled during a full build. Its obsolete product module is now removed, the native flashlight declares the package override, and stale output is removed before rebuilding. The legacy source APK remains available for porting; the release image must contain only the replacement.
