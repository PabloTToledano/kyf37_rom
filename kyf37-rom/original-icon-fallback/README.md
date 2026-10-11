# Original app icon fallback — 2026-10-11

All custom launcher themes now retain the original activity icon when the app has no custom mapping, has only a generic placeholder mapping, or its artwork cannot be loaded. This applies to root and folder tiles. Existing custom mappings remain themed.

Source: `device-inspection/fix-android10-original-icon-fallback.py`, automatically staged after Classic theme generation by the serialized build wrapper. Java loader regression checks: `device-inspection/verify-original-icon-fallback.py` (unmapped, generic, missing/corrupt artwork and theme cache passed). Launcher build passed in 2:07.

Installed with `adb install -r`; live Home remained focused, crash buffer empty. `live-unmapped.png` shows IR Remote's original wrench icon alongside themed icons. APK SHA-256: `6f6266d21cac04367d406cfae16b0a50f6b23e68e36fdd32d08ec1455d95802d`.

Rollback: install `Kyf37Home-before.apk` with `adb install -r -d`. Folder/theme preferences are retained. The already-flashed v22 ZIP is unchanged; a future freshly built ROM includes this source fix.
