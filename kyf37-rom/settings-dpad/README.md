# Settings D-pad corrections — 2026-10-10

## Findings and changes

MasterSwitchPreference has two actions: the row opens details and widget_frame
owns the toggle click handler. The child switch was focusable but non-clickable,
so it could receive OK without running the real action. It is now non-focusable;
Right on the row focuses widget_frame, OK uses its existing change listener, and
Left returns to the row. Controller vetoes and disabled/admin checks are retained.

SettingsBaseActivity prepares visible, enabled clickable secondary actions for
keypad focus before dispatching keys, without making decorative children separate
targets. RecyclerView can consume Up at its first selectable row instead of
letting focus reach the master SwitchBar. The app now routes that boundary Up
to the visible enabled bar. Category headings are skipped when determining the
first actionable row. Other keys retain normal dispatch, including sliders,
editors, dialogs and ordinary switch preferences.

During hardware testing, Connected devices crashed because UsbBackend assumed a
USB framework service was present. It is absent on this running ROM. Null guards
report no ports/functions instead; the page can now open. This does not add a USB
service or change the functioning ADB connection.

## Reproduction and release

Idempotent source: `device-inspection/fix-android10-settings-dpad.py`, automatically
run by the normal locked build wrapper. Build Settings using build-locked.sh.
The raw image validator now hashes product/priv-app/Settings/Settings.apk against
current output, so a future ZIP cannot silently carry an older Settings build.
No new full ROM image/ZIP built here; existing ZIPs are unchanged.

Live installer: `tools/install-settings-dpad.ps1`. Only an APK update, no flash,
framework replacement, system remount or reboot. Backup: Settings-before.apk
(SHA-256 af3b69d86cab3fce89ee61219c49aff18d2e00ffe7413f17260f1d688c5c301d).
Rollback while holding the phone lock: adb -s 981108631314 install -r -d
kyf37-rom/settings-dpad/Settings-before.apk. Userdata is retained.

## Hardware checks

Network & internet: Right focuses the actual secondary widget_frame, Left returns
to the parent row; decorative switch focusable=false confirmed by UI hierarchy.
Wi-Fi was not toggled or modified. Captions: D-pad Down + OK changes the real
secure accessibility_captioning_enabled value to 1, then OK to 0; originally
absent key restored with settings delete. Location master bar: OK changes
location_mode 3 -> 0 -> 3 (original state restored). Connected devices opens
successfully after the USB guard. Earlier crash and first-row/category boundary
test failure led to the corrections described above.

These checks do not establish every screen or third-party app is keypad-ready.
Changes are scoped to Settings; other apps and custom-drawn controls remain
outside this patch. No security restrictions or lockscreen authentication bypass.

Final build passed (1:55, BUILD_EXIT=0) and final APK installed live.
SHA-256 7bac2a6e67c930fc251302747027a8a5f1812aab00f22af36a65f7647b563910.
Location Down/Up returned focus to switch_bar with category headings present
(location-final.xml). Screenshot toggle-final.png visually confirms a clear
pink/white focus outline on the independent switch action after Right.
Final states: location_mode=3, captions key absent, bluetooth_on=1, boot_completed=1,
/system read-only. Phone lock released. No flash or reboot. The original APK
backup remains available. Full future-image validator not run on a new systemimage.
