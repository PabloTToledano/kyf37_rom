# Keypad navigation, focus theme and Clear-deletes-text (2026-10-09)

Goal (owner): the whole base system usable from the keypad; selected item unmistakable; Clear deletes a
character in a text box; pointer mode only an optional fallback. **Not packaged into any ZIP; the v18 hold
is untouched.** Framework parts need a full ROM flash; status below is honest about what ran where.

## Scripts (all idempotent, WSL Python 3, chained into `build-kyf37-android10.sh` in this order)

| Script | What it does |
|---|---|
| `fix-android10-focus-theme.py` | Adds `android.view.Kyf37FocusTheme` (palettes, `Settings.Global kyf37_focus_theme` observer, drawing), makes `View.drawKyf37KeypadFocus` delegate to it (old yellow/navy look gone), adds `Kyf37BackDel`/`Kyf37BackDelPolicy` and `ViewRootImpl.Kyf37BackDelStage`, makes SystemUI logical selections (notification rows, QS tiles) use `Kyf37FocusTheme.selection()`. Run after `fix-android10-keypad-panel.py`. |
| `fix-android10-visible-focus.py` | Now a no-op (superseded; avoids reintroducing yellow). |
| `fix-android10-pointer-cursor.py` | Redesigned pointer (F3): arrow with theme-accent body, dark keyline, white halo + soft shadow, 26 dp, press scale + expanding ring (140 ms ease), recolours live. |
| `fix-android10-keypad-nav-ui.py` | Home / Phone settings / Outer-screen settings stop drawing their own blue/yellow selectors when the framework theme exists (legacy selector kept on older ROMs); installs the shared Appearance page; overlay `kyf37_keypad_nav.xml`: `config_defaultInTouchMode=false` (windows open in keypad mode, so first focus is visible) and spinner date/time pickers (NumberPicker: D-pad + digits). |
| `audit-keypad-focus.py` | Read-only static audit of layouts (Settings, SettingsLib, SystemUI, framework dialogs, DocumentsUI). Result in `kyf37-rom/keypad-nav-audit.json`: ~25 hits, nearly all the correct "focusable row + non-focusable switch/checkbox inside" pattern; no layout needed changing. |
| `test-kyf37-back-del.sh` | Host unit test of the Clear rule (14 checks, passes). |
| `tools/test-keypad-nav.ps1` | On-device checks (cycle all 7 palettes with screenshots, Back-deletes test via `debug.kyf37.back_del_any`, pointer). Run only after the framework is flashed, under the phone lock. |

Sources: `device-inspection/Kyf37FocusTheme.java.txt`, `Kyf37BackDel*.java.txt`, `Kyf37FocusCompat.java.txt`,
`Kyf37AppearanceSettings.java.txt`. Build helper: `start-keynav-build.sh <log> <targets...>`.

## Clear/Back rule (framework, `ViewRootImpl.Kyf37BackDelStage`, first stage of every window's input pipeline)

Applies to BACK with scan code 355 (physical Clear). If the focused view is an editable `TextView` (incl. password),
a custom editor (via its InputConnection) or the lock-screen `PasswordTextView`, and it has a selection or text before the
cursor, the key becomes a synthetic **DEL** (backspace) down+up that goes through the full pipeline, so TT9 (IME visible or
hidden) handles it as a normal backspace and clears its composing word. Cursor at the very start with text after it sends
FORWARD_DEL. Empty field / no editor / WebView / read-only: normal Back. Never traps: any probe error means normal Back.
Why here: only the app process can see the focused editor's content; PhoneWindowManager (system_server) cannot, and
rebuilding TT9 was ruled out by the owner. The IME stage runs after it, so the IME sees plain DEL.
The deletion fires on key **release**; auto-repeat is swallowed. This keeps hold-Clear = Memo pad exactly as before
(PhoneWindowManager swallows the release after a long press, so nothing is deleted). Trade-off: holding Clear does not
repeat-delete.

## Focus theme

`Settings.Global kyf37_focus_theme` (userdata, survives updates; default 0). 0 Sky blue, 1 Pink, 2 Mint green, 3 Orange,
4 Purple, 5 Monochrome (black outline, white edge), 6 Bold (7 dp black outline, 3 dp cyan edge, strong cyan tint).
Look: translucent tint over the item + 4 dp accent outline + 2 dp white edge outside it (so it reads on light and dark
wallpapers); bold uses 7+3 dp. One class draws it for all Views, ListView/GridView selected rows, SystemUI logical
selections and the pointer; a per-process ContentObserver invalidates everything on change (no reboot).
Choose it in Settings > Appearance or Phone settings > Appearance (same activity, 7 options with colour swatches).
Large containers (scroll views, lists, web views, whole-screen views) are never outlined.

## Coverage and limits

* Done: View/ListView/GridView (all apps, dialogs, Settings, SystemUI windows, keyguard PIN keys, Home grid), notification and
  QS selections, pointer, Appearance page, picker modes, initial focus on open (non-touch default).
* Exists in AOSP and not changed: PIN digits/DEL/Enter on the lock screen, legacy Recents D-pad navigation, SeekBar left/right,
  NumberPicker up/down.
* Known gaps: the volume panel is a non-focusable window (hardware volume keys work, its settings button is not
  reachable by keypad); spinner DatePicker still shows a CalendarView next to the spinners; WebView text fields get plain Back;
  third-party apps with custom-drawn UI cannot gain focus. A page-by-page walk of every Settings screen was **not** done.

## Verification status

* Host: `test-kyf37-back-del.sh` passes. Audit run complete.
* Build: see "Build result" at the bottom (updated after the queued build).
* Hardware: **nothing verified on the phone yet.** Framework pieces (selection look, Back rule, pointer, touch-mode default,
  pickers) are only testable after a full flash. Only the APK-level pieces (Phone settings Appearance page, Home) can be
  installed live (`sign-test-apk.sh` + `adb install -r`, phone lock held); SystemUI must NOT be installed on the v17 framework
  (it calls the new framework class).

## Build result
`build-locked.sh` (framework services framework-res SystemUI Kyf37Home Kyf37PhoneSettings), log `/home/pablo/keynav-build.log`: BUILD_EXIT=0. Artifacts (not installed, framework.jar must NOT be copied alone): `kyf37-rom/keypad-nav/`. Settings app was not rebuilt (only a summary string changed); a full systemimage build is still needed before v19.


## v18 audit and v19 fixes (2026-10-09, keypad-nav agent) — screenshots in `kyf37-rom/keypad-nav-v18/`

Full `systemimage` build via `build-locked.sh` (log `/home/pablo/v19-keynav-full-build.log`): **BUILD_EXIT=0** (29:29). Not packaged, not flashed.
All new scripts are chained into `build-kyf37-android10.sh` (loop `focus-theme pointer-cursor keypad-nav-ui home-cursor focus-polish settings-homepage-focus setupwizard-keypad default-permissions adb-default`).

| # | Owner complaint | Root cause (found on the v18 phone) | Script | Status |
|---|---|---|---|---|
| 1 | No cursor on Home | Grid cells are background-less layouts => `PFLAG_SKIP_DRAW`: `View.draw()` (where the theme hook lives) never ran. Same bug hides the selected row in the power menu and other list dialogs | `fix-android10-home-cursor.py` (Home: `setWillNotDraw(false)`, initial selection, Up/Down wrap at grid edges) + `fix-android10-focus-polish.py` (framework: lists paint their own selected row, `AbsListView.dispatchDraw -> Kyf37FocusTheme.drawListRow`) | Home APK **verified on hardware** (selected tile + moves in all directions, wrap; `home-nav-*.png`, `after-home.png`). Framework list part: built only |
| 3 | Status bar always outlined | `config_defaultInTouchMode=false` gives the non-focusable status-bar window a default-focused view and the hook outlined any focused view; also the notification shelf strip in the open shade | `home-cursor.py` (`hasWindowFocus()` required) + `focus-polish.py` (only interactive views are outlined: clickable / long-clickable / text editor / seek bar / number picker / checkable / spinner; containers never) | Built only (framework). Still visible on v18 until flashed |
| 2 | Setup wizard not D-pad friendly | Clickable-but-not-focusable rows (date/time, privacy, SIM), no initial focus, long flow | `fix-android10-setupwizard-keypad.py`: all clickable views focusable, initial focus on NEXT (lists keep list focus), Menu/F1 = Next, flow cut to Welcome, Language, Date/time(+time zone), Wi-Fi, Finish (dropped: Bluetooth intro, SIM/mobile data, privacy/metrics, biometric, screen lock, restore; originals kept as `lineage_wizard_script.xml.orig-kyf37`) | APK installed live and **hardware-verified** page by page via direct activity launches (Welcome focus on NEXT; Language list + NEXT; Date/time order tz -> date -> time -> NEXT; spinner date dialog with visible focus). The shortened chain itself (script change) and Wi-Fi page were not exercised on hardware (components are disabled after setup; `user_setup_complete` was set 0 temporarily and restored to 1) |
| 4 | General keypad audit | Settings homepage rows unreachable (`blocksDescendants` in `settings_homepage_container.xml`; Up/Down only scrolled); power-menu rows invisible (above) | `fix-android10-settings-homepage-focus.py` | Settings APK installed live, **hardware-verified** (row highlighted, D-pad moves). Audited OK on v18: dialer (digit field focus), Settings sub-pages (Wi-Fi, Display, Date, Bluetooth, Apps, Sound, Security: initial focus + moves), shade/QS (tile selection), date picker. Not done / still open: volume panel (non-focusable window), generic digit shortcuts for numbered rows (only Home 0-9 exist), PIN lock-screen walk, share sheet, permission prompts (now moot, item 5), dedicated "go to status bar" key |
| 5 | Apps ask for permissions | `grantPermissionsToSysComponentsAndPrivApps` only covered sys components / platform priv apps; 49 runtime perms of 20+ system apps were ungranted on v18 (`perms-ungranted-before.txt`: TT9, Dialer, Contacts, Gallery, Email, Etar, Aurora, Jelly, Magisk, ...) | `fix-android10-default-permissions.py`: framework grants every runtime permission of every FLAG_SYSTEM package (revocable; runs on first boot, on build-fingerprint change/flash, and for new users = also after data reset) + `etc/default-permissions/default-permissions-kyf37-all.xml` fallback (list + dialer/messaging/camera sets) | **Live on v18: all 49 granted with `pm grant`** (`perms-ungranted-after-live-grant.txt` has 1 line left: companiondevicemanager COARSE_LOCATION, restricted). Framework policy + XML: built only; pending flash. Packages updated later (e.g. Aurora self-update) are not re-granted until the next fingerprint change / new user |
| 6 | USB debugging always on, any computer | `ro.adb.secure=1` in the boot ramdisk `default.prop` => "unauthorized" with an unreachable dialog | `fix-android10-adb-default.py`: patches `package-android10-legacy-boot.py` (`ro.adb.secure=1 -> 0` in default.prop, written before any other assignment) + `device.mk` fallback `ro.adb.secure=0`, `persist.sys.usb.config=adb` (AdbService sets `adb_enabled=1` whenever that persist prop contains adb, also after data reset). ro.debuggable/root unchanged | **Takes effect only after the v19 BOOT image is packaged with this script and flashed** (ramdisk change). Not exercised. Live phone already has adb_enabled=1 (set by the lead) |

Live changes made to the phone (all revocable / app-level): Kyf37Home, Settings and LineageSetupWizard APKs updated (`Kyf37Home-signed.apk` etc. in `kyf37-rom/keypad-nav-v18/`, platform-signed, `adb install -r -d`); 49 runtime grants. `screen_off_timeout` was temporarily set to 10 min and put back to 30000. SystemUI/framework were NOT touched live. Phone lock released.

Tools: `kyf37-rom/keypad-nav-v18/shot.sh` (keys + screenshot), `probe.sh` (launch intent, focused node before/after DOWN).

## Settings D-pad controls corrected — 2026-10-10
Installed APK-level fix, no flash/reboot: split-action rows use Right to focus
actual toggle, OK invokes existing controller, Left returns to row; decorative
non-clickable switch no longer steals focus. Dynamic clickable secondary actions
are made focusable. Up from first actionable list row reaches master SwitchBar,
including pages with noninteractive category headings. USB-service null guards
also prevent Connected devices page crashing on this live ROM.
Source/replay: device-inspection/fix-android10-settings-dpad.py (build wrapper).
Future raw image validation now checks current Settings.apk hash. Final locked
Settings build passed 1:55; final APK installed and tested. D-pad-only checks:
Right/Left independent switch focus, visible focus screenshot, Captions OK 1->0
(original absent key restored), Location OK 3->0->3, first-row Up to master bar,
Connected devices opens. Wi-Fi not toggled. System RO, phone lock released.
Artifacts, exact coverage/limits and rollback APK: kyf37-rom/settings-dpad/README.md.
Scope is Settings, not a claim that every screen or third-party app is fixed.

## Modern native D-pad lockscreen — 2026-10-10
Installed without flash/reboot: rounded tonal clock card, wallpaper-derived pastel
accent, large clock, selected Unlock pill and explicit Up/Down notification guide.
Up/Down selects Unlock/native notification; OK unlocks through native Keyguard or,
after native authentication completes, invokes the full native notification
launcher (work-profile/pending-intent/autocancel checks retained). Bouncer input,
PIN/password verification and notification privacy remain native.
Source/replay: device-inspection/fix-android10-modern-lockscreen.py plus
Kyf37LockActions.java.txt and Kyf37LockscreenKeys.java.txt. Build wrapper applies
it after navigation staging; existing SystemUI image hash gate covers next ZIP.
Final build passed 2:15; source idempotence confirmed across 37 files. Hardware:
clock/card geometry, wallpaper cyan palette, Up/Down selection, OK unlock, and
Down+OK Discover Trust -> native TrustOnBoardingActivity verified. Initial tall
layout/alpha, notification spacing and native row-click failures are documented.
Final SystemUI PID 9033, /system RO, own phone lock released. Local test
notification/channel removed, original root state restored. No new ZIP built.
PIN/password and redaction not tested because no credential is configured; no
wallpaper-change test. Material You-inspired styling, not Android 12 Monet/full
Material 3 conversion. Artifacts, screenshots and exact rollback:
kyf37-rom/modern-lockscreen/README.md; installer tools/install-modern-lockscreen.ps1.

## SystemUI Material You pass - 2026-10-11 (sysui-material agent)
Live-installed SystemUI-m8 (sha256 5a4d63af...675d): Material You look on shade, QS tiles, notification cards, footer, volume/power themes, keitai badges and sparkles kept.
Selection is now `Kyf37Material.selection` (thick rounded focus-colour outline plus tonal fill). Keypad logic untouched, but the real shade walk is NOT re-verified
(the SIM-PIN keyguard blocks it); see KEITAI-MATERIAL.md "Honest status" and the preview harness.
