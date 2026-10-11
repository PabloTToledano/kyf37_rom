# Pixel-inspired native lockscreen — 2026-10-11

The owner disliked the enclosing square/card. It is removed from both the XML
background and runtime wallpaper listener. The native TextClock now floats over
the wallpaper: 104sp stacked hours/minutes while idle; 62sp horizontal time when
native keyguard reports visible notifications. Date, alarm/status indications,
carrier, charging and native lock icon remain. A small translucent outlined OK
chip retains an explicit D-pad target, without enclosing the clock in a panel.
This is a Pixel-inspired layout using available Roboto, not Google's proprietary
font or an Android-version upgrade. The newer Material SystemUI shade is retained.

## Source and release

`device-inspection/fix-android10-modern-lockscreen.py` stages the action/key
templates and calls `fix-android10-pixel-lockscreen.py` last. The build wrapper
already calls the modern script after all navigation/Material staging. Changes
cover refreshFormat, density updates and notification transitions, so a native
clock refresh cannot restore the old horizontal idle layout. Native time format,
current-user handling and tick scheduling remain in TextClock; no new timer.
Existing SystemUI image hash validation covers the next freshly built ZIP.
No ZIP, boot or recovery image was built/flashed in this session.

Locked SystemUI build passed in 2:19 (`build.log`). Installed APK SHA-256:
`c8637c4c778543379ea3a5460a361615a726b8a28d39c4f93cbd467a9e720a81`.
Exact pre-session Material m8 rollback is `SystemUI-before.apk`, SHA-256
`5a4d63af8ccfbbdedfe5e9a98d91438e46934262726498e8eef12966c850675d`.
Installer: `tools/install-pixel-lockscreen.ps1`, atomic system APK replacement,
WP helper, rollback and SystemUI-only restart. The first read-only remounts
returned EBUSY, including after restart; a later retry succeeded and `/system`
was checked RO. Installer now retries the final remount. No reboot was required.

## Hardware evidence and limits

* `idle.png`: real native lockscreen, stacked clock, wallpaper visible, no card.
* `notification.png`: real local test notification causes compact clock; native
  date/actions and notification fit without overlap. `selected.png`: Down selects
  the notification. Native OK unlock was exercised during app testing.
* Root-context notification attempts returned/no-op'd; a real shell-UID
  `cmd notification post` succeeded after temporary adb unroot. Root was restored;
  only our `kyf37-lock-test` tag/id2020 and helper channel were removed. DND and
  lockscreen privacy settings were retained.
* SIM was initially reported secure, later LOADED with native secure=false; no
  PIN was entered, guessed or bypassed by the agent. Credential/bouncer code is
  unchanged, and credential-protected authentication/redaction is not tested.
* Main SystemUI PID remained 18918 through the live checks. New clock source was
  applied twice; Python compilation and wrapper Bash syntax passed.

Rollback uses the same system-copy procedure with this folder's before APK;
preserve all existing other rollback copies. APK updates require the phone lock.

Final replay check: check-replay.py ran all three session staging scripts twice; 12 APK/source payload hashes stayed identical (replay-validation.log). Final device check: boot_completed=1, SystemUI PID18918, adb root, system RO, org.kyf37.dialer default. Phone lock released; final.png is the final installed idle screen.

