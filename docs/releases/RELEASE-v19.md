# KYF37 Android 10 Go v19

Owner-specific release for serial 981108631314. Built from the tree on 2026-10-09 after the v18 first-boot failure.

## What changed since v18
- **Boot fix kept:** `public.libraries-kyocera.txt` is not in the image (it aborted zygote in v17) and the One Seg TV apps
  (`FsDtvApp`, `Kyf37Tv`) are not in the image (FsDtvApp crash-looped on a missing `libskia.so` in v18). The release gate
  `device-inspection/check-release-image.py` is part of packaging and checked both.
- **Keypad / keitai UI:** selection colour theme (Settings > Appearance, `kyf37_focus_theme`: Sky blue, Pink, Mint, Orange,
  Purple, Monochrome, Bold), no more yellow; visible selection on Home; status bar outlined only when navigated to;
  Settings homepage rows reachable by D-pad; setup wizard operable with D-pad; Clear/Back deletes a character when a
  text field has text, else Back; redesigned pointer (F3) as an optional fallback.
- **Permissions:** all runtime permissions of pre-installed apps are granted by default at framework level (revocable).
- **ADB:** USB debugging on by default, `ro.adb.secure=0` (any computer accepted) and root via adb for testing.
- Includes the camera and sound fixes, Magisk (v23, runtime daemon), microG signature-spoofing fix, outer-screen timeout and
  settings, the new kernel and matching modules.

## Known gaps (honest)
- Not booted on hardware before packaging. First boot takes minutes; test with `tools/test-keypad-nav.ps1`.
- No `su` binary is shipped in `/system/xbin`; root for shell is via `adb root` (persist.sys.root_access=3 must be set; see AGENTS.md).
- Volume panel, share sheet, IME picker and the PIN screen were not walked by keypad. Digit shortcuts for numbered rows exist on Home only.
- Cellular does not register (modem never starts NAS/UIM/WMS/VOICE/WDS). B20 is set in the LTE mask.
- GPS engine starts but a fix needs an outdoor test.
