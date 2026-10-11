# Launcher app management — 2026-10-11

The Home launcher now supports persistent hiding of apps from Home and folders. Select an app with the D-pad, press `*`, choose **Remove from launcher**, then confirm. This does not uninstall the app. Use `*` → **Restore hidden apps…** to restore one app or all apps to Home. Hidden app component IDs are stored alongside the existing layout preferences; refreshing the launcher no longer adds them back.

Additional keypad improvements:
- Move mode handles navigation before GridView consumes the D-pad and OK keys.
- `0` / `#` jump backward / forward by a screen of grid rows.
- A persistent footer shows the active controls; `*` → **Keypad help** explains the shortcuts.
- `*` → **App info…** opens the native Android app details screen.
- Returning from another app exits stale move mode before reloading the grid.

Reproduction: `fix-android10-home-management.py` updates the canonical Home template idempotently. The build wrapper runs it immediately before `fix-android10-home-redesign.py` installs that template. Build with `device-inspection/build-locked.sh /home/pablo/home-management-build.log Kyf37Home`.

Deployment and keypad hardware validation are pending while the phone lock is held by `claude-battery`. No phone mutations were performed for this change. Native authentication and default dialer are retained.

Validation: the final Kyf37Home module build completed with `BUILD_EXIT=0`; log: `kyf37-rom/home-management-build.log`. A rerun of the management script leaves the canonical Java source byte-identical. The platform-signed app update is staged at `kyf37-rom/Kyf37Home-management.apk`. Install and hardware tests remain pending due to the active phone lock. The final build also consumes the key release after finishing move mode, preventing accidental grid activation.

Hardware checklist after installation under the phone lock: remove an app from Home and a folder; revisit Home and restart the launcher to confirm persistence; restore one and all; test the empty launcher Options menu; move a tile with physical D-pad/OK and verify it does not launch on release; page with 0/#; check App info, help, folder Back, Call and corner keys. Do not clear launcher data during validation.
