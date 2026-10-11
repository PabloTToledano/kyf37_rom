# Visual keypad settings — 2026-10-08

Package: `org.kyf37.keypad`; activity: `.KeypadSettings`.

The settings list is replaced with a keypad arranged like the owner's KYF37 photo: Contacts/Mail on the left, Camera/Apps on the right, a central directional pad and OK key, Call/Clear/End, a 3-column number pad, F1/F2/F3, and a separate exterior side key. The cream background, rounded ivory keys, and sage focus outline give it a neutral, soft appearance.

Use the D-pad to focus a key and Select to open its action picker. The selected key and assigned action appear beneath the keypad. The picker marks the current choice and saves immediately. Default removes the override. Lid sleep, pointer speed, and confirmed reset remain available below the keypad. All 28 existing scan mappings and the existing action choices are preserved; no framework behavior or boot receiver is changed by this patch.

## Reproduce

Apply `device-inspection/fix-android10-visual-keypad-settings.py` using WSL Python after any original keypad creation/mapping scripts. The script is re-runnable and skips an already-patched app. It optionally accepts an alternate app directory for isolated compilation.

Build with `bash device-inspection/build-visual-keypad-settings.sh` inside WSL, using its `/mnt/c/...` path. Do not run concurrently with another Android build. This builds the platform-signed app using the existing ROM platform certificate and does not use the owner's boot signing key.

WSL source: `/home/pablo/kyf37-android10/packages/apps/Kyf37KeypadSettings/src/org/kyf37/keypad/KeypadSettings.java`.
Build log: `/home/pablo/kyf37-visual-keypad-build.log`.
Previous installed APK backup: `device-inspection/Kyf37KeypadSettings-before-visual.apk`.

## Verification

The Java source passed isolated compilation against the Android 10 framework classes. Re-running the patch reports that it is already applied. Final APK and hardware verification status are recorded below when completed.

Final build succeeded in 2m55s. Exported platform-signed APK with embedded `classes.dex`:
`C:\Users\pablo\Documents\ChatGPT\flipphone_roms\device-inspection\Kyf37KeypadSettings-visual.apk`

SHA256: `a507b34cccfb70d4757d873fdff1d699d85e20b0841aaaaa61940a53f0100097`.

Hardware installation/launch was attempted after export, but ADB returned `no devices/emulators found`. The redesigned app has not been installed or visually verified on the phone in this turn. No ROM was flashed. The existing `system.img` predates this app patch; a full image must be rebuilt before packaging a ROM release with it.

### ADB installation follow-up — 2026-10-08

ADB installation now succeeded (`adb install --no-streaming -r`, output `Success`). Package Manager confirmed the updated package at `/data/app/org.kyf37.keypad-C5odh9ytE9UPXorsOypG0g==/base.apk`. `am start` accepted the activity intent. The phone was unstable during this session: it restarted before installation and later lost its input service/ADB connection during screenshot and D-pad verification. Focus was StatusBar when checked, so successful visual rendering and action-picker navigation are still unverified. No mappings were changed during testing.

### Button settings branding and hardware verification — 2026-10-08

Renamed the screen title and launcher app label to **Button settings**; the source Settings entry uses the same title. Added an adaptive cream/sage vector keypad icon with ivory buttons and a small gold sparkle, plus a fallback vector icon. Re-runnable patch: `device-inspection/fix-android10-button-settings-branding.py` (apply after visual keypad patch).

Updated APK: `C:\Users\pablo\Documents\ChatGPT\flipphone_roms\device-inspection\Kyf37ButtonSettings.apk`.
SHA256: `c412c32b98dc7f40dbf622791631f1e8a501005e25ba651c79eb444be6dfa8c3`.
Build passed in 43 seconds; ADB installation returned Success. Verified app activity focus, screen title and layout in `device-inspection/button-settings.png`. Select opened the current-action picker (`button-settings-picker.png`), then Back dismissed it without changing any mapping. The launcher displays the new name and icon (`button-settings-home-top.png`). This supersedes prior pending visual/picker verification. No action persistence change was tested in this follow-up. The source Settings entry requires a future Settings/system build to update the already-installed Settings app entry.
