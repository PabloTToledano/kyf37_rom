# Keypad flashlight — 2026-10-09

Replacement package: `org.kyf37.flashlight` / `Kyf37Flashlight.apk`.
Legacy package: `jp.kyocera.mobilelight` / MobileLight.

The current revision has one large flashlight illustration and ON/OFF status.
Only the center/OK button toggles the light (Enter is an equivalent key code).
There are no On/Off buttons or directional menus. Held-key repeats do not toggle
repeatedly. Back switches off and exits; leaving the app or SCREEN_OFF requests
Off. The display stays awake while the light is on.
The app uses CameraManager's torch API on a worker thread and observes torch
callbacks. It shows camera-busy/errors and retains the last known light state if
an operation fails. It does not write directly to the vendor's encoded LED node.
Android's camera service also owns torch cleanup when its client process dies.

The illustration follows Standard/Pastel/Sky Star selection. Home maps the new
package to the existing flashlight icon in both custom packs.

## Install and old-app removal

**Phone changes are currently deferred at the owner's explicit request to
continue without phone access.** The final APK is built and ready, but the latest
single-center-button update has not been installed and the old app has not been
removed from the current phone user.

When phone access is allowed, run `tools/install-keypad-flashlight.ps1`. It:

1. Acquires the phone lock and preserves original Home/MobileLight APK backups.
2. Installs Kyf37Flashlight and the updated Home package map.
3. Grants the foreground flashlight app its required CAMERA permission.
4. Removes MobileLight for user 0 only after confirming the replacement exists.
5. Opens the replacement app and releases the phone lock.

The old preinstalled system APK is kept as a rollback copy on the current ROM;
`pm uninstall --user 0` removes the installed app for the owner. A clean future
ROM build excludes MobileLight and includes Kyf37Flashlight instead. No system
partition write, recovery/boot flash or user-data wipe is needed for installation.
`-KeepLegacy` is available for diagnosis before removal; normal runs remove it.
`-SkipInstall` can finish removal after the replacement has already been updated.

Rollback: reinstall the saved Home APK, remove `org.kyf37.flashlight` normally,
then use `cmd package install-existing --user 0 jp.kyocera.mobilelight` to restore
the preinstalled old app. This cannot recover app-private data deleted by uninstall.

## Rebuild

Run `device-inspection/fix-android10-keypad-flashlight.py` in WSL after the earlier
stock-app port/icon scripts. Then build `Kyf37Flashlight Kyf37Home` through
`device-inspection/build-locked.sh`. The source script is rerunnable; it registers
the module, substitutes it in device.mk, stages a default CAMERA permission grant,
and updates both Home theme package maps. `--source-only` stages the Activity for
small follow-up builds. The Activity source template is
`device-inspection/Kyf37Flashlight.java.txt`.

## Verified and pending

- Initial build: passed, 2:06; initial APK and Home installs: passed.
- Torch On/Off on hardware: CameraService recorded the new app's PID 3491
  switching the torch on; vendor LED brightness changed 0 → 1 → 0.
- The initial screenshots show real callback-driven ON/OFF states. Their names
  predate the single-button revision, so they are not previews of that revision.
- Previous focus-highlight build: passed, 13 seconds. Final APK SHA256:
  768240fa2e9586c6576e45099a8d758075b93d16358c5f74ebee9128805e7009.
- Pending: final APK installation, lid/Back lifecycle hardware checks, final UI
  screenshots, old-package removal and duplicate-launcher verification.

Testing was interrupted by a system_server ART JIT crash loop. Another on-device
test script (`/data/local/tmp/st.sh`) was concurrently sending D-pad events, and
JIT properties changed back to true after a temporary documented JIT-off recovery.
The phone's package service was intermittently absent, so final install attempts
were rejected. `runtime-crash.txt` preserves evidence; this was not a Java crash
of the replacement app. The owner then instructed work to continue without phone
access. No further phone operations were performed, the torch was last read as 0,
and this session's phone lock had been released.

## Latest single-center-button revision
Both flashlight and SystemUI builds passed (initial 3:08 and final follow-up).
The final APK replaces the two-button artifact; previous APK is saved as
Kyf37Flashlight-two-buttons.apk. SHA256SUMS lists the current hashes.
Hardware evidence above refers to the initial two-button implementation only.
The unchanged CameraManager backend was previously verified; this new interaction
has not been tested on the phone. The old-app removal remains pending.


## Installed on owner's request — 2026-10-09
Latest single-button flashlight and SystemUI installed successfully. Legacy
jp.kyocera.mobilelight removed for user 0; rollback system APK retained.
Center torch toggle hardware readings: 1 then 0. Notifications visible, expanded
QS visible with gold tile selection, and large lock clock verified by screenshots
keypad-panel-live.png, keypad-qs-live.png, keypad-lock-live.png in keitai-systemui.
SystemUI PID 6961 remained running, /system read-only, LED off, own lock released.
Attempted auto-rotation tile test left accelerometer_rotation at 1 throughout;
selection/action was not conclusively verified, so do not claim a toggle-state
change. Incoming heads-up and full tile-action coverage remain unverified.
No ROM/boot/recovery flash; updated the application APKs only.
