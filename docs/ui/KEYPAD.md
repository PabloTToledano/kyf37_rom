# KYF37 keypad guide (Android 10 ROM, v12+)

Photo reference: the owner's keypad (Japanese legends). Key identities were **captured on the real phone**
(`device-inspection/keypad-capture-all.txt`, `getevent -l /dev/input/event1`, 2026-10-08).

## Physical keys -> Linux scan codes

| Printed key | Scan | Linux name | Android effect |
|---|---|---|---|
| Contacts (book icon) | 59 | KEY_F1 | **Opens Contacts** |
| Camera (top-right) | 60 | KEY_F2 | **Opens Camera** (original Kyocera camera) |
| Mail (envelope, "AF lock") | 61 | KEY_F3 | **Opens Messages**; hold = Email |
| Apps (globe, "アプリ") | 62 | KEY_F4 | **Opens the icon-grid Home**; hold = Recents; **hold + digit = quick launch** |
| Bottom **F1** | 63 | KEY_F5 | Menu |
| Bottom **F2** | 64 | KEY_F6 | Recent apps |
| Bottom **F3 / POINT** | 65 | KEY_F7 | Toggle the on-screen pointer (cursor) |
| D-pad, centre | 28 | KEY_ENTER | Select / Click (in pointer mode) |
| D-pad left/right "copy" icons | 105/106 | KEY_LEFT/RIGHT | Normal left/right |
| Clear (クリア) | 355 | KEY_CLEAR | **Back**; hold = Memo pad ("メモ" legend) |
| Call (ペア legend) | 231 | KEY_SEND | Call / answer / dial pad; hold = Bluetooth pairing ("ペア") |
| End (⏻ legend) | 116 | KEY_POWER (qpnp_pon) | End call; **Home outside a call**; hold = power menu |
| Side key | 254 | KEY_CAMERA | Lid closed: show outer clock; lid open + unlocked: **notification shade** |
| `1`..`9`,`0`,`*`,`#` | 2-11, 55, 253 | KEY_1.. | digits / `*` / `#` (see below) |

Lid open answers an incoming call. The earlier mapping where the Mail key toggled the pointer was a mistake and is gone.

## Quick launch with digits

* **Home grid** (press Apps/End to get there): tiles are numbered; press `1`-`9` (tile 1-9) or `0` (tile 10) to open it.
  Long-press `#` on the Home grid toggles ringer <-> vibrate.
* **Anywhere:** **hold the Apps key and press a digit**:

| Digit | Default app |
|---|---|
| 1 | Phone (dial pad) |
| 2 | Messages |
| 3 | Camera |
| 4 | Contacts |
| 5 | Browser |
| 6 | Memo pad |
| 7 | Sound recorder |
| 8 | Flashlight |
| 9 | Settings |
| 0 | Barcode reader |

Change a slot (value is a package, `package/Activity`, or one of `tel: sms: contacts: browser: email: settings:`):

```
adb shell settings put secure kyf37_quick_5 org.mozilla.firefox
adb shell settings delete secure kyf37_quick_5      # back to default
```

The Apps+digit combo and the four corner keys are ignored while the lock screen is showing.

## Soft-key legend (bottom bar, one compact row)

`F1 Menu | F2 Recent | OK Select | F3 Pointer` (in pointer mode: `OK Click | F3 Exit`). It mirrors the printed bottom row.

## Where it lives (for maintainers)

* `frameworks/base/services/core/java/com/android/server/policy/Kyf37QuickKeys.java` - scan-code based role table, long press timers.
* `PhoneWindowManager.java` - `mKyf37Quick` hook just before the per-scan remap block in `interceptKeyBeforeQueueing`.
* `Kyf37Navigation.java` - pointer toggle ignores scan 61.
* `device/kyocera/kyf37/keylayout/matrix_keypad_67.kl` - 63 MENU, 64 APP_SWITCH.
* `SystemUI .../Kyf37SoftkeyBar.java` - the legend.
* `packages/apps/Kyf37Home` - icon-grid launcher; `packages/apps/Kyf37KeypadSettings` - per-key remapping for the non-quick keys.
* Patch script: `device-inspection/fix-android10-quick-keys.py` (idempotent; run in WSL).

## Phone settings app (keypad first)

`packages/apps/Kyf37PhoneSettings` ("Phone settings", opens from Menu/F1 on the Home grid and from Apps-hold + `9`).
Rows are numbered: press the digit to jump to the row and activate it.

| Key | Row | Behaviour |
|---|---|---|
| 1 | Wi-Fi | toggle on/off in place |
| 2 | Bluetooth | toggle on/off in place |
| 3 | Ringer | cycles Ring -> Vibrate -> Silent |
| 4 | Brightness | cycles 8% / 24% / 43% / 67% / 100% |
| 5 | Screen timeout | cycles 15 s / 30 s / 1 min / 2 min / 5 min |
| 6 | Date & time | opens Android settings page |
| 7 | Language & keyboard | opens page |
| 8 | Battery | opens page |
| 9 | Keypad & keys | opens the per-key remapping app |
| 0 | All settings | opens the full Android Settings |
| (list) | Sound & volume, Storage, Apps, About phone | D-pad + OK |

Source: `device-inspection/Kyf37PhoneSettings.java.txt`, installed by `fix-android10-phone-settings-app.py`.
## 2026-10-08: owner wallpaper and Home wallpaper support

Hardware-verified: KYF37 Home now displays Android's wallpaper instead of an opaque dark background. White clock, date, and app labels have shadows for readability. Owner's attached blue sky/stars/castle image is set for FLAG_SYSTEM | FLAG_LOCK, at 480x854; both Home and the actual keyguard were screenshot-verified after sleep/wake. Android uses the system image for both when no separate lock wallpaper exists; this is expected for a combined setStream call. On-device wallpaper_orig SHA256: 27a18d28fdd6f48444e6c8f4eba71c80fef071e066244bf584b08275f714d43e (matches staged image).

Reproducible source: device-inspection/fix-android10-home-wallpaper.py (run after launcher-generation scripts). Updates Home.java and its Windows template, stages the attached image as the ROM default and a launcher asset, and adds the explicit WallpaperSetup activity. Normal launcher starts never overwrite user-selected wallpapers. The helper needs both SET_WALLPAPER and SET_WALLPAPER_HINTS; the first live attempt lacked the latter and failed safely, corrected before application.

Live launcher compiled successfully through build-locked.sh, then its manifest was repackaged by build-home-wallpaper-live.sh and platform-signed with sign-test-apk.sh. Installed with adb install -r -d device-inspection/wallpaper/Kyf37Home-wallpaper.apk. Apply explicitly with adb shell am start -a android.intent.action.VIEW -f 0x10008000 -n org.kyf37.home/.WallpaperSetup. The VIEW action/new task avoids the ROM's Home-task intent behavior. Original launcher APK retained in wallpaper/Kyf37Home-before-wallpaper.apk. Screenshots: wallpaper/home-verified.png and wallpaper/lock-verified.png. Source persists for future ROM builds; no new installer ZIP was created or flashed. Full build log: /home/pablo/home-wallpaper-build.log.
