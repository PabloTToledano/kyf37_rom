# Keitai lockscreen and notifications — 2026-10-08

> Later owner policy (2026-10-09): no generic bottom bar; native Kyocera guides
> only in supported apps. Home large clock removed. NATIVE-SOFTKEYS.md documents
> the final scripts, build persistence, image gates and offline validation status.

The Android SystemUI retains notification delivery, per-app content intents,
notification privacy and the existing Keyguard authentication. This patch adapts
the presentation and physical-key controls for the KYF37 non-touch screen.

## Interaction

- Standby: framed dark clock/date area, monospace clock, white type, OK unlock hint.
- Unlocked notifications: Up/Down selects a real notification row, with a blue
  outline and automatic scrolling. OK invokes the existing notification click.
- Right/Left expands/collapses content or groups. Expanded group children can be
  selected individually. DEL dismisses only notifications Android marks clearable.
- The side key continues to open/close the shade. Back continues to close it.
- A bottom guide distinguishes locked and unlocked operation. Notification rows
  have thin outlines. Existing wallpaper, notification privacy and security stay
  under Android control. No alternative lockscreen app or listener is installed.

The design uses the standby and physical-key notification interaction documented
in the [original GRATINA manual](https://www.au.com/content/dam/au-com/guide/document/kyf37_basic_e.pdf)
as inspiration, rather than claiming to reproduce its firmware exactly.

## Reproduction

Run `device-inspection/fix-android10-keitai-systemui.py` in WSL after the earlier
keypad-unlock/softkey patches. Build `SystemUI` via `build-locked.sh`. Copy
`out/target/product/kyf37/system/product/priv-app/SystemUI/SystemUI.apk` to
`kyf37-rom/keitai-systemui/SystemUI.apk`. Run `tools/install-keitai-systemui.ps1`.
The installer backs up the installed APK before updating it. Future ROM builds
include these SystemUI source changes. No boot image or ROM flash is needed.

SystemUI is persistent: Android rejects `adb install -r` for this package.
The installer uses the documented temporary system-WP helper, remounts /system,
atomically replaces only SystemUI.apk, preserves old oat files, then restarts
SystemUI and remounts read-only. Rollback uses the same system-copy procedure
with the saved APK and oat directory from `/data/local/tmp/keitai-systemui-rollback/`.
Keep the original backup; do not overwrite it on reruns. No protected modem,
recovery, boot, or user-data partitions are changed.

## Verification

Passes 2-6, run in order after the first script: `fix-android10-keitai-systemui2.py` (flat square
rows, square selection, `M/d (EEE)` date, locked softkey "OK Unlock"), `...systemui3.py` (keitai info
header replacing the touch Quick Settings header, opaque pale backdrop), `...systemui4.py` (legends
follow keyguard state, shade guide hidden while locked), `...systemui5.py` (header count refresh),
`...systemui6.py` (no empty navy strip on the lockscreen).

Hardware-verified 2026-10-09 (screenshots in `kyf37-rom/keitai-systemui/`): `p5-s.png` shade (header
time / `10/9 (Fri)` / count 2, flat framed rows, key guide), `p5-h.png` Home (softkeys back to
F1/F2/OK/F3), `final-lock.png` lockscreen with pass 6 (APK sha256 f20ecdf6...).

Known defects: the status-bar strip above the shade header renders black with a clipped clock;
lockscreen rows are flat but not framed (keyguard uses a different row background). The phone
rebooted once right after the pass-6 install (uptime 31 s) and came back normally; cause not
investigated (known rare kernel/ext4 resets, see AGENTS.md section 6).

Rollback APKs: `SystemUI-before-keitai.apk`, `-pass1`, `-pass2`, `-pass3`, `-pass5`. The installer now
resets `$LASTEXITCODE` (fresh `powershell -File` runs failed with "Phone is in use").

## Final continuation — 2026-10-09

Pass 7 (`fix-android10-keitai-systemui7.py`) extends the header to cover its full
176dp area, removing the clipped status-clock strip. Built with the Sky Star
integration build (4:02, BUILD_EXIT=0), installed, and screenshot-verified:
`final-notifications.png` shows the clean header and zero-count empty state.
Final APK SHA256: 7513c32a544645c0607a6324291797bc96b1bac7c7f8f46e155ccffea639b941.

Hardware checks: D-pad selected rows, Right expanded a test notification, Left
collapsed it, OK opened the native Trust preferences activity, and DEL removed
the test notification (the shade then collapsed because it was empty). Native
OK unlock was rechecked after waiting for its transition: showing=false.
`test-expanded.png`, `test-cleared.png`, `final-lock.png` preserve evidence.
No PIN/password is configured, so a secure credential challenge was not tested;
the existing bouncer remains in control. Group support compiled but a multi-child
notification group was not generated on this run.

Notification shell posting must run as UID 2000: root adb triggers a null-package
channel exception. Temporary `adb unroot` fixed the test; original root adb state
was restored. SystemUI is stable (PID 8014), boot_completed=1, /system read-only,
and the phone lock was released. Older black screenshots were captured after the
ten-second lockscreen timeout, rather than indicating a SystemUI crash.


## D-pad panel redesign — 2026-10-09 (offline)
The owner reported missing notifications and quick settings. The old 176dp
painted header covered native QS and could obscure content near the top. The new
`fix-android10-keypad-panel.py` removes that overlay and uses native notification
rows, heads-up delivery and Quick Settings. F2/Menu switches between notifications
and expanded QS. In QS, directional keys cycle visible native tiles with a gold
selection border; OK invokes the native tile action. In notifications, Up/Down
selects rows, OK opens, Left/Right controls details, DEL dismisses clearable rows.
The native QS state labels and toggle backend remain in control. Additional QS
pages/detail navigation are not implemented by this patch.
Standby clock uses sans-serif-light, tighter spacing and 76sp text including the
handset height-qualified resources. Native OK unlock and credential bouncer remain.
Run this script after passes 1–7; rerunning older passes afterwards overwrites it.
Phone access remains paused at the owner's instruction. Installation, incoming
notification/heads-up verification, tile actions and lockscreen visual QA pending.

Both offline builds passed; final SystemUI.apk saved in kyf37-rom/keitai-systemui/.
Previous pass-7 build saved as SystemUI-before-keypad-panel.apk. The existing
install-keitai-systemui.ps1 targets the updated APK; it has not been run.


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


## Visible focus and stock phone port — 2026-10-09 (offline continuation)
User requested unmistakable system-wide focus and original keypad phone app.
fix-android10-visible-focus.py adds navy/yellow/corner focus to native Views and
selected ListView rows; SystemUI gets matching layered outlines. keypad-panel.py
now uses spatial tile navigation, actual QS expansion state and initial selection.
Framework/SystemUI build passed 9:14; final SystemUI passed 2:53. Artifacts and
limitations: kyf37-rom/keypad-focus/README.md. Not installed; framework update must
use a validated ROM/matching ART image set, not an isolated framework.jar copy.

Stock phone test port: port-stock-dialer-android10.py, stock-resource-compat.py,
class and Telecom audits. Isolated org.kyf37.dialerxx; old default retained.
New APK rebuild includes resource-ID remapping and legacy class dependencies;
static class resolution passed (one generic metadata descriptor excluded). Telecom
method audit still finds OEM/legacy APIs absent in Android 10, so not production
ready and not selected as default. No call placed. Early APK installed and reached
permission review; revised APK not installed. See stock-dialer-port/README.md.
Another phone session launched Camera/Calendar despite lock; owner explicitly
chose continued offline work. All ADB activity then stopped; local lock released.

## Native-only bars / clock removal final offline builds - 2026-10-09
SystemUI/Home/framework-res passed 2:53; services/native apps passed 2:01.
Compiled showNavigationBar=false, default navigation dimensions=0dp. All six
native APKs passed bridge/artwork verification. Ten artifacts, logs, SHA256SUMS
and deployment limits saved in kyf37-rom/native-softkeys/. NATIVE-SOFTKEYS.md
is the source/rebuild/persistence handoff. No installation or new ROM ZIP; no
phone testing after the owner's explicit offline instruction. Default dialer stays.

## Focus theme and Clear rule - 2026-10-09
Yellow/navy focus replaced by the shared theme android.view.Kyf37FocusTheme (SystemUI selections use it). Status, scripts and limits: KEYPAD-NAV.md.
Not installed, not hardware-verified.

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

## Pixel-style lockscreen — 2026-10-11
The enclosing clock card is removed; stacked idle / compact notification native clock installed. Material shade retained. See kyf37-rom/pixel-lockscreen/README.md for source, evidence, native-auth limits and exact rollback. This supersedes the rounded-card appearance described above.

