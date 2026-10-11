# Modern native keypad lockscreen — 2026-10-10

Material You-inspired keyguard, implemented inside native Android 10 SystemUI.
Rounded dark tonal clock card, medium-weight clock, rounded filled Unlock action,
explicit keypad instructions, and a wallpaper-derived pastel accent. Uses
WallpaperManager.getWallpaperColors (lock wallpaper, system fallback), with an
attached-only color listener; no polling, bitmap processing or new dependency.
This is not Android 12 Monet or an OS-wide Material 3 port.

Up/Down selects Unlock or a visible native notification. OK on Unlock delegates
to StatusBar.onSpacePressed, the existing native bouncer path. OK on a notification
invokes its existing native click handler; Android retains authentication and
notification visibility rules. Credential screens and dozing are excluded from
the new key handler. No credential data, lock settings, PIN/password verification,
redaction or dismissal rules were changed. Media/Back/digit handling stays native.

Reproducible source: device-inspection/fix-android10-modern-lockscreen.py and
Kyf37LockActions.java.txt / Kyf37LockscreenKeys.java.txt. The build wrapper applies
this after the keypad-nav chain so older UI staging does not overwrite it.
Normal SystemUI asset hashing in the image validator covers the next fresh ZIP.
Existing ZIPs unchanged; no new full systemimage or ZIP generated here.

Install: tools/install-modern-lockscreen.ps1, using the cooperative phone lock,
temporary system-WP clear, atomic APK replacement, context/ownership restoration,
sync/remount read-only and SystemUI restart. No boot/recovery flash or reboot.
Exact old APK: SystemUI-before.apk; device backup:
/data/local/tmp/modern-lockscreen-rollback/SystemUI.apk. Rollback under the lock
using the same WP/remount/context/atomic-copy procedure with that backup, then
restart SystemUI. Optional old oat files are backed up if present; the current
phone had oat-stale instead of an active oat directory.

Preflight app_process reflection confirmed the live framework provides
android.view.Kyf37FocusTheme.selection(Context), which the existing shade source
uses. No isolated framework jar update is needed.

Owner currently has no PIN/password configured (Keyguard secure=false). Secure
credential entry must not be claimed hardware-tested without a credential test.

First live iteration exposed a native layout assumption: getMaxClockY placed the
larger keypad status card at negative Y, so getClockAlpha returned zero and both
card and notification area appeared blank. Native OK unlock still worked. Fixed
within SystemUI's KeyguardClockPositionAlgorithm by clamping KYF37 max clock Y to
at least its existing minimum top margin. Other devices and authentication logic
are unchanged. Do not repeat the first APK without this positioning correction.

Second iteration displayed the card and OK unlocked correctly, but the tall
status area left no native notification capacity. The final layout uses native
responsive clock sizing (compact 54sp height-qualified sizes), compact padding/hint, and zero height for the unused invisible clock-icon
container (view ID retained). Actual notification rows/shelf, filters and privacy
are still native; no rows are forced past security visibility checks.

Removing the unused icon space also required supplying the full card height to
NotificationPanelView's position algorithm on KYF37 (the stock calculation
subtracted half of the old icon shelf). This prevents the first row overlapping
the lower edge of the card. Current screenshots verify the final geometry.

The existing Discover Trust notification's row click did not launch while locked,
including a native injected tap. Unlocking first and posting the row click also
failed to open it. The final keypad path requests native
StatusBar.dismissKeyguardThenExecute with afterKeyguardGone=true, then posts to
the existing NotificationActivityStarter.onNotificationClicked pipeline on the
main thread. That retains native pending-intent, work-profile challenge, bubble,
remote-input and auto-cancel behavior. It does not directly send a launch intent
or skip credentials. Visual/logical selection resets to Unlock after activation.

## Final hardware verification

Final locked build passed in 2:15 (BUILD_EXIT=0), build.log. Installed live with
SystemUI restart only, no reboot/flash. Installed APK and host artifact SHA-256:
`2913e2cd24b7ae43011b65c34b4fb5c107ae9db2751ffe8d463f722816961d9b`.
Original APK SHA-256: `d4598b8822f18056e265d7d8139ea7956e1bf4e1305c9ff2386b23b729cfe88e`.

Screenshots verified rounded card, current-wallpaper cyan accent, large clock,
selected Unlock pill and notification outline with no overlap. Up/Down moves
between Unlock and a visible native notification. OK unlock verified:
Keyguard showing=false. Down + OK on Discover Trust opened
org.lineageos.lineageparts.trust.TrustOnBoardingActivity with Keyguard
showing=false (controlled-notification-test.txt). Test notification was posted
locally, then its own tag/channel removed; no messages sent to anyone. This
notification was not the selected row in the successful launch check, which
opened the real existing Trust notification instead. Shell notification posting
with a content intent failed its caller-package check; the contained Java helper
was used for posting and cleanup. ADB root state restored.

Final SystemUI PID 9033, boot_completed=1, /system read-only, no FATAL EXCEPTION
in the final 200-line log check. Phone left on the new lockscreen, own lock
released. Final idle image: final.png; notification highlight: selected-final.png.
The staging script ran twice with hashes unchanged for 37 relevant source files.
Python compilation and build-wrapper syntax checks passed. Existing image hash
gate covers the next fresh ZIP; no new full systemimage/ZIP was built here.

Limits: no credential configured, so secured PIN/password entry and redacted
notifications were not hardware-tested. The native bouncer/verification/filtering
code remains in control. Palette rendering was verified for the current wallpaper;
live wallpaper changes were not exercised. This does not convert all system apps
to Material 3 or provide Android 12's system-wide Monet engine.
