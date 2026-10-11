# Shipped Kyocera app compatibility — 2026-10-11

See [live test report](../all-stock-app-ports/LIVE-20261011.md) for exact tests,
source replay and remaining blockers. Artifacts include Camera, recorder, MemoPad
and MemoPadProvider update APKs and exact pre-update copies. These were installed
with adb install -r -d, preserving app data. No framework/boot/recovery flashing.

Replay scripts are chained after native-softkey staging in the locked build
wrapper: fix-android10-stock-storage-api.py and
fix-android10-selected-stock-runtime.py. Future fresh system images include the
changes; existing selected-app image hash gates reject stale APK copies.
Existing ZIPs unchanged. Data APK overrides also persist across normal ROM updates.

Rollback: under the phone lock, adb install -r -d the corresponding before APK.
Do not uninstall providers or clear app data. Keep both before/current APKs.
The stock dialer provider blocker and incomplete Notepad editor are documented,
not hidden behind fake success. Recorded test audio and one test photo were left
on the phone; existing media/notes were not deleted.
