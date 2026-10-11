# KYF37 secondary screen implementation and extension guide

## Verified behavior and current deployment

On 2026-10-08 the owner confirmed that the secondary screen displays correctly after the corrected native renderer was applied. The physical visible panel is **128 × 36 pixels**, monochrome. `/sys/class/graphics/fb1/virtual_size` reports **128,72** because two framebuffer pages are allocated; this is not the visible resolution. Treating that allocation as a 128 × 72 screen was the previous rendering bug.

The running phone was tested using a temporary bind mount of `libkyf37subdisplay-height36.so` over `/system/lib/libkyf37subdisplay.so`, followed by restarting `org.kyf37.subdisplay/.OuterScreenService`. This mount disappears on reboot. The corrected files are also in the Android source and the full image rebuild is in progress. Owner confirmation proves the live correction; it does not yet prove installation from the final ROM ZIP.

## Source locations

Android source tree in WSL: `/home/pablo/kyf37-android10`.

- `packages/apps/Kyf37OuterScreen/src/org/kyf37/subdisplay/OuterScreenService.java`: service, clock/battery state, lid visibility, minute alarm, native call.
- `packages/apps/Kyf37OuterScreen/src/org/kyf37/subdisplay/WakeReceiver.java`: alarm/boot receiver; consult manifest for registered actions.
- `packages/apps/Kyf37OuterScreen/AndroidManifest.xml`: service/receiver declarations, system UID and permissions.
- `packages/apps/Kyf37OuterScreen/controller.c`: JNI entry and panel descriptor/power control.
- `packages/apps/Kyf37OuterScreen/framebuffer.c`: validates hardware geometry, maps memory and commits a frame.
- `packages/apps/Kyf37OuterScreen/render.c`, `render.h`: monochrome clock/battery drawing, no Android UI dependency.
- `frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java`: publishes lid state and handles the exterior side key.
- Kernel reference: `/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/disp_ext_sub*.c`.

Workspace native-source mirror: `kyf37-rom/navigation/subdisplay/`. Both this mirror and the Android tree were updated. The old integration script copies this mirror into the Android tree; do not run it blindly over newer Java service changes.

Correction script: `device-inspection/fix-android10-subdisplay-height.py`. It changes geometry and replaces the clock layout; review before rerunning. Test library: `device-inspection/libkyf37subdisplay-height36.so`.

## Event and rendering path

1. The kernel reports lid events to Android input policy.
2. KYF37 policy publishes `sys.kyf37.lid_open`: `true` for open, `false` for closed, and starts/refreshes the explicit outer-screen service. Search `publishKyf37LidState` in the current framework source for the exact integration points.
3. The service reads that property. The current source renders whenever the lid is closed and blanks while it is open.
4. Time/date changes, timezone changes and battery broadcasts refresh the frame. Battery percentage is computed from broadcast level and scale.
5. While closed, an exact `AlarmManager.RTC_WAKEUP` alarm schedules the next minute boundary. The receiver starts the service again. Open lid cancels that alarm.
6. The exterior key maps to `KEYCODE_CAMERA`. While closed, policy starts the service with `org.kyf37.action.OUTER_WAKE`, consumes the key, and leaves the main screen asleep.
7. `refresh()` holds a bounded 3-second partial wakelock around the native operation, releasing it in `finally`.
8. JNI `updatePanel(visible, hour, minute, battery)` opens fb1, unblanks if needed, renders and commits. Invisible state blanks and closes the descriptor.

The Java source retains historical `visibleUntil`, `wasClosed` and delayed-blank fields. The current visibility expression is simply `visible=closed`; the old ten-second timeout no longer controls the display. Remove these obsolete fields coherently when extending the service, rather than assuming they remain an active timeout mechanism.

## Framebuffer contract

- Device: `/dev/graphics/fb1`, framebuffer identifier `subdisplay`.
- Visible dimensions: **128 × 36**; 16 bits per framebuffer pixel.
- Line length: **256 bytes**.
- Virtual allocation: two pages, normally 128 × 72.
- Renderer output: exactly **4,608 bytes**, one byte per logical pixel, restricted to values 0 or 1.
- Native conversion: logical 1 becomes `uint16_t 0x0010`; logical 0 becomes zero. The original kernel extracts `(pixel & 0x0010) >> 4`. This is not ordinary RGB565 white.
- Commit: obtain fixed/variable information with `FBIOGET_FSCREENINFO` and `FBIOGET_VSCREENINFO`; validate device ID, dimensions, bpp, stride, offsets and mapping size; map with `mmap`; write the selected page; call `FBIOPAN_DISPLAY`; unmap.
- Power: `FBIOBLANK` with `FB_BLANK_UNBLANK` or **`FB_BLANK_NORMAL`**, matching the OEM driver's accepted states. Other blank modes are not supported by this driver.
- Native functions return errors. Service logs `Panel update failed: <negative errno>` under **`KYF37OuterScreen`**. Do not silently suppress errors or assume an ioctl success proves a visible image.

Render functions clip pixels to `0 <= x < 128`, `0 <= y < 36`. The current layout places HH:MM at y=2 with 3× scaled 5×7 digits, then battery graphics at y=26–35. Keep all new elements inside this visible range.

## Extending functionality

For a new clock style, date or icon, change `render.c` first. Keep the renderer independent of framebuffer access and produce only binary pixels. Test the whole 4,608-byte buffer with guard bytes, bounds and value checks; generate a PGM preview for visual inspection. The old preview test used 128 × 72 and must be updated before reuse.

For notification badges or call state, gather real state in the service using the appropriate Android API and permissions. Store a compact snapshot, refresh only when it changes, and pass explicit fields to JNI. Update Java native declaration and C JNI signature together. Do not use private notification contents without a deliberate display policy.

For alternate pages, define an explicit page model and use a dedicated protected action or key event to select pages. Do not repurpose the closed-lid side key in a way that wakes the main screen. Avoid a second process writing fb1 concurrently; the native controller assumes serial calls on the service main thread.

For animation or second-resolution time, choose a bounded refresh policy and account for suspend/battery cost. Current minute wakeups are intentional. Avoid keeping the CPU awake continuously. If adding background-thread rendering, serialize all descriptor and panel state operations; the present static descriptor is not thread safe.

For timeout/backlight behavior, distinguish panel visibility from actual illumination. The live owner test confirms visible output; no separate illumination control is established here. Trace the original driver/stock service before inventing a backlight node. Reconcile `panel_on` with any new external power transitions.

Preserve the privileged service boundary, explicit component routing and existing permission protection. New external broadcasts should be protected or checked. Keep model-specific framework behavior limited to KYF37.

## Build and validation

Rebuild `Kyf37OuterScreen` and `libkyf37subdisplay` in the configured Android build environment, then rebuild `systemimage`. Framework key/lid changes also require the framework services build. Use the project's full image validation, signing, installer and rollback procedure before flashing a complete ROM; a successful app/library compilation alone is insufficient.

Useful device checks (ADB serial **981108631314**):

```text
adb -s 981108631314 shell getprop sys.kyf37.lid_open
adb -s 981108631314 shell cat /sys/class/graphics/fb1/modes
adb -s 981108631314 shell cat /sys/class/graphics/fb1/virtual_size
adb -s 981108631314 shell dumpsys activity services org.kyf37.subdisplay
adb -s 981108631314 shell logcat -d -s KYF37OuterScreen
```

Verify open/closed transitions, side key while closed, minute rollover, timezone changes, low/high battery, service restart and suspend/resume. After installing a final image, reboot and repeat these tests with no temporary bind mount. Record owner-observed output separately from host-side ioctl/log evidence.


## Side-key mapping fix — 2026-10-08

The owner confirmed that closing the lid and pressing the side key now lights the outer clock. Raw input from `qpnp_pon` (`/dev/input/event2`) is Linux scan code **254**, mapped to Android **CAMERA** by `qpnp_pon.kl` (also present in `gpio-keys.kl`). PhoneWindowManager intercepts a physical CAMERA press with the lid closed and starts OuterScreenService using `org.kyf37.action.OUTER_WAKE`; it consumes the key so the main screen stays asleep.

Android 10 key layouts do **not** accept the old `WAKE` or `WAKE_DROPPED` flags. Their presence made the entire OEM layout fail parsing, and EventHub fell back to Generic.kl. This broke the side key and other board-specific key assignments. Remove these flags from all board layouts; implement wake behavior in framework policy and the kernel wake IRQ instead. Do not re-run older scripts that add WAKE flags.

Verified after one zygote restart: EventHub selected `qpnp_pon.kl`, `matrix_keypad_67.kl`, and `swic_hs_key.kl`. Owner then verified the side key. Corrected files were persisted on `/system/usr/keylayout/`, not left as temporary bind mounts; originals are in `/data/local/tmp/kyf37-keymap-wifi-backup/`. System was synced and remounted read-only. The ROM source and rebuilt system image contain the same corrected layouts. A reboot-based verification is still required.

## 2026-10-08: lid sleep and stock opening/closing feedback

Root cause on the live phone: Settings.Global lid_behavior=0 (LID_BEHAVIOR_NONE), so lid events updated the outer display but did not sleep the main display. Set lid_behavior=1 (LID_BEHAVIOR_SLEEP) persistently; also explicitly enabled existing Settings.System open_sound_enabled and close_sound_enabled. No reboot, ROM flash or /system write required.

Verified on hardware via injected EV_SW/SW_LID events on gpio-keys /dev/input/event8: value 1 closes, value 0 opens. Closing updated sys.kyf37.lid_open=false and power state to Asleep / display OFF; opening restored true and Awake / ON. First close reported last sleep reason lid_switch; later cycles sometimes reported timeout from the existing policy sleep wrapper, but all closed-state measurements were OFF. Closed-lid physical side-key scan 254 injection left main display OFF. Event state restored open after tests; physical folding was not directly observed by this agent.

The installed /system/media/audio/ui/open.mp3 and close.mp3 are byte-identical to stock (SHA256 2bbf1ba99fc557bdbf7574ba2a8f086666800f5e65e308b1faf25d74bd66ff15 and 35255b4bdeeb3290a37c7be3a3f01f9fdce7ec28570a76a4dd18700177036436). Existing Kyf37Feedback SoundPool playback piid 31 produced started events for both transitions; AudioFlinger added separate 44.1kHz stereo tracks with 69120 close / 70272 open frames. Ringer remained normal, system stream unmuted at 5/7. Audibility is supported by playback telemetry, not a microphone recording or human confirmation; silent/vibrate behavior remains respected.

Reproduce live: device-inspection/apply-lid-sleep.ps1. Source default for future clean installations: device-inspection/fix-android10-lid-sleep.py adds config_lidControlsSleep=true, which SettingsProvider maps to lid_behavior=1. Existing userdata needs the live setting (already applied). No new ROM ZIP created. The previously running full wallpaper build began before this source overlay update; future image builds must rerun after both wallpaper and lid scripts.

## 2026-10-08: second side-key press plays a cute outer-screen animation

Installed and hardware-tested via the real input-policy route using EV_SW lid events and physical side-key scan 254 injection. While closed: first side-button press shows/refreshes the clock and arms a 10-second second-press window; pressing again within that window plays a bouncing/blinking round friend with twinkling stars. 24 monochrome frames at 150ms spacing, nominally 3.6 seconds, deadline 4.5 seconds. The animation returns to the clock automatically; a third press cancels it; opening the lid cancels and blanks fb1 immediately. Main screen remains asleep/OFF while animating. No continuous animation or high-frequency background alarm; partial wakelock bounded to 6 seconds and released on completion/cancellation.

Source script: device-inspection/fix-android10-outer-animation.py (run after old subdisplay generators). Java template: OuterScreenService-animation.java.txt. Native render.c/render.h/controller.c mirrored under kyf37-rom/navigation/subdisplay. New explicit JNI updateAnimation(int frame) uses the same serial main-thread panel owner and existing validated framebuffer commit function. No framework or key mapping change needed.

Verification: verify-outer-animation.py compiles the pure renderer with GCC -Wall -Wextra -Werror and checks all 24 frames, guard bytes, binary pixels and invalid arguments. Preview: device-inspection/outer-animation/preview.gif. Android module build through build-locked.sh /home/pablo/outer-animation-build.log Kyf37OuterScreen libkyf37subdisplay completed successfully, BUILD_EXIT=0. Build wrappers now accept optional module targets, retaining bootimage/systemimage defaults and cooperative flock.

Live APK: package-outer-animation-live.py bundles the matching native display library and libc++.so and platform-signs. First live attempt omitted libc++.so and service crashed because data-app linker namespace excludes that platform library; corrected by bundling the matching built runtime, then reinstalled and verified stable. No /system writes or ROM flash. Current source/library files are ready for the next fresh ROM ZIP; existing ZIPs are unchanged. Backup original APK: outer-animation/Kyf37OuterScreen-before.apk.

Hardware test script: test-outer-animation-live.py (hold phone lock). All assertions passed: frames differ from clock and each other; clock restored after completion and third press; main display OFF during animation and ON after opening; animation wakelock released in both paths. Raw fb1 captures, decoded hardware-frame.png, and hardware-verification.json retained in device-inspection/outer-animation/. This proves framebuffer output and event handling; physical panel appearance was not judged by human eyes. Input lid state restored open after testing.

Build history note: earlier full wallpaper build reported "build completed successfully (20:29)" but its wrapper subsequently reported BUILD_EXIT=127 because build wrapper files were updated while that old shell was reading them. Both current scripts pass bash -n and the subsequent targeted animation build completed with BUILD_EXIT=0. Future complete ROM builds should use the current wrappers and re-run all desired patches before packaging.

## 2026-10-08: owner Mametchi reference replaces the round friend

The owner supplied a black/white Mametchi sprite. Its 14x16 pixel grid was reconstructed from the attached reference and rendered at 2x scale (28x32), with paired ears, broad face, large highlighted eyes and tiny limbs. Bounces fit within 128x36 without clipping, blinks on frames 10/11, alternates a waving hand, with surrounding sparkles. Reference preserved at device-inspection/outer-animation/mametchi-reference.png. Updated idempotent script fix-android10-outer-animation.py and native source mirrors. Current preview: outer-animation/preview.gif.

Build /home/pablo/outer-mametchi-build.log completed in 10s, BUILD_EXIT=0. Updated APK installed live; all existing renderer bounds/invalid-input checks and on-phone frame-change, clock-return, third-press cancellation, lid-open cancellation, wakelock-release and main-display-OFF tests passed. Rebuilt source is ready for the next fresh ZIP. User-perceived appearance on the physical OLED remains for owner judgment; framebuffer captures confirm the installed sprite.

## 2026-10-08: softer Mametchi eyes and a clock interaction scene

Owner requested less creepy eyes and a transition from clock to character and back with character interaction. Replaced huge hollow eyes with a light filled face, small dark eyes, a smile, blink and happy squint. New native scene takes the real current hour/minute/battery from Java: frame 0 is the standard clock; frames 1-7 slide clock away and reveal the character; 8-15 bounce/blink; 16-19 travel left; 20-31 pull the actual clock back by its right edge; 32-38 wave beside restored clock and exit; frame 39 is exactly the standard clock. Forty frames at 100ms, with the existing 4.5s deadline / 6s bounded wakelock. Third-press and lid-open cancellation retained.

Native template extracted to device-inspection/outer-animation-render.c.txt, installed idempotently by fix-android10-outer-animation.py; JNI updateAnimation and renderer signatures now include frame/hour/minute/battery together. Pure-renderer verification checks all 40 bounded binary frames plus exact first/last equality with the clock. Android targeted build /home/pablo/outer-clock-scene-build.log succeeded, BUILD_EXIT=0. APK installed live and all hardware smoke tests passed again (changing frames, clock return, cancellation, wakelock release, main display OFF during animation / ON on opening). Current preview.gif updated. Source is staged for the next fresh ROM build; existing ZIPs unchanged.

## 2026-10-08: 42 reference-sheet scenes and an animated default clock

Owner supplied a Mametchi activity/costume sheet and requested as many references as practical, varied coherent scenes, an animated default clock and a new scene on EVERY side-button press. Supersedes the second-press/third-press rules above. Reconstructed 71 monochrome poses across 42 named scene groups with extract-outer-reference-sprites.py; source reference-sheet.png, generated reference-poses.h and reference-scenes.json retained in device-inspection/outer-animation/. Each scene cycles only its own pose group (eating, fishing, bath, brushing teeth, instruments, clothes, wings, etc.). Shuffled bag traverses all 42 before replenishing and avoids an immediate repeat across replenishment. Pressing during a scene replaces it with a new one.

Default display now has a smaller readable clock/battery on the left and a gently breathing/looking-around Mametchi on the right, with occasional sparkle. Idle exact wakeup alarm is every 5 seconds, matching Android alarm minimum-futurity behavior; only a short update wakelock is held and released, no continuous idle wakelock. Opening cancels both scene and idle alarm and blanks fb1. Scene transitions use the real time/battery and slide away from the idle clock, show the selected activity, then the friend reaches for/pulls the clock back and exits; 48 frames at 100ms, 6-second deadline and bounded 8-second wakelock. Idle animation resumes after scene completion.

Pure renderer checks: all 42 scenes/2016 frames, guard bytes, binary pixels, invalid frame/scene bounds, exact first/last idle-clock equality and at least three distinct idle states. verify-outer-animation.py passed. Initial Java compilation caught an incorrectly expanded updatePanel declaration, corrected before installation; current Android build outer-variety-final-build.log succeeded in 11s, BUILD_EXIT=0. The initial hardware test sampled idle too early for the alarm minimum-futurity; corrected idle period to 5 seconds and aligned hardware test timing. Latest test-outer-variety-live.py passed all assertions: idle animates, four button presses yield different scene frames, main display remains OFF, scene wakelock released and idle resumes, lid opening cancels and main display wakes. Results in variety-hardware-verification.json. Native app APK updated live; no ROM flash. Source is ready for a fresh next ZIP build; existing ZIPs unchanged.

Preview GIF and variety-preview.png show selected reference activities. Physical OLED appearance remains for owner judgment; verified actual framebuffer samples and input behavior. Phone cooperative lock released after testing.

## 2026-10-08: remove duplicate actor and smooth scale transitions

Owner observed overlapping characters. Root cause: the animation's sliding clock bitmap included the idle character, while a separate scene actor was drawn on top. The renderer now strips the actor region from the clock layer and renders exactly one actor separately. Character enters by interpolating from its idle position/size to a larger activity pose (target 31px high, proportional width capped at 60px), then gradually shrinks and settles back beside the clock. Return path no longer sends a second actor off-screen; actual first/last idle frames remain exact matches. Skating movement corrected to the skating scene index (31).

All 42 scenes / 2016 native frames passed bounds/binary/clock-endpoint checks. Preview of beginning/middle/return/end retained in outer-animation/seamless-preview.png. Android build /home/pablo/outer-seamless-build.log completed in 1m05s with BUILD_EXIT=0; matching APK/library installed live after completion. Early hardware runs used fixed sampling delays and intermittently missed asynchronous idle updates/scene completion; hardware test now polls boundedly for those conditions instead of treating a missed sample as failure. Source changes are in the idempotent renderer template and native mirrors for the next fresh ROM build.

Final on-phone seamless-version hardware run passed all checks: animated idle, four new scene samples, internal display OFF, bounded completion and idle resumed, opening cancellation and main wake. Results updated in variety-hardware-verification.json.

## 2026-10-08 — Larger clock / compact battery / lower-right return
- Native renderer now uses a 21-pixel-high clock (previously 14), a 16x6 battery footer, and an idle character at x=106 with bottom=34.
- Activity return interpolates to that new resting position; clock restoration takes 16 frames and keeps the idle actor out of the clock layer.
- All 42 scenes / 2,016 frames passed native buffer and endpoint checks; targeted Android build succeeded (`~/outer-clock-layout-build.log`). Packaged APK: `device-inspection/outer-animation/Kyf37OuterScreen-animation.apk`.
- Live installation remains pending: Android was restarting before installation and blocks waiting for `android.hardware.sensors@1.0::ISensors/default`. ANR saved as `device-inspection/outer-animation/window-startup-anr.txt`. A clean reboot and sensor-service restart did not establish stable window/storage services; installer fails because StorageManager is unavailable. No partitions were flashed or userdata wiped. Do not claim this layout is installed or included in an existing ZIP.

## 2026-10-09 — Long side-button Bad Apple mode (installed)
With lid closed, hold the side button 800ms to interrupt the character scene and play the full Bad Apple video and song locally. A single press stops both and restores the animated clock; a held stop does not restart. Short presses outside playback retain shuffled character scenes. Lid-open/audio-focus loss cancel; existing media volume is respected. Original 4:3 silhouettes are centered 48x36 inside the 128x36 display, 15fps, 219 seconds, compressed assets about 1.5MB. A playback-specific SCREEN_ON guard prevents apps waking the inner panel while the lid remains closed.
Final build and live installation succeeded. All physical-event/framebuffer/audio-player/wakelock/button/lid checks passed, including an injected wake staying OFF. Full-length test passed: active at 213.3s, automatically completed by the 228.5s polling sample, inner display OFF throughout, player/wakelock released. Earlier attempts encountered a recovery round-trip (trigger unknown) and camera audio-focus interruption; both are documented honestly in `device-inspection/outer-animation/BAD-APPLE.md` with saved evidence.
Source: `fix-android10-outer-badapple.py` after the animation generator (the latter invokes it when media assets exist); conversion `prepare-bad-apple.py`; repeatable live installer `tools/install-outer-badapple.ps1`. Media provenance/hashes/licence notes: `third-party/bad-apple/`. Existing ZIPs unchanged; source and assets staged for the next fresh build. Rollback APK preserved; no partition flash.

## 2026-10-09 — Correction: Bad Apple audible-silence fixed
Earlier player/activity tests did not prove audible music. The owner's report exposed a real audio HAL ABI mismatch: stock HAL's 36-byte pcm_config final avail_min was interpreted as Android 10's inserted silence_size (40-byte config). ALSA rejected SW_PARAMS; AudioFlinger still reported started/nonzero audio while hardware PCM was closed. Scoped pcm_open translation for audio.primary.msm8909.so fixes it. Script `device-inspection/fix-android10-audio-pcm-config-abi.py`; library rollback/provenance/guard-page regression and precise before/after evidence in `device-inspection/audio-pcm-compat/README.md`. Built, installed and clean-reboot verified: kernel PCM RUNNING with advancing pointers, speaker DAC On, full button/audio release checks pass, fixed hash persisted, system RO. Existing ZIPs unchanged; next-build source fixed. This corrects earlier music verification wording; physical listening was not performed.

## 2026-10-09 — Wider Bad Apple framing (built, installation pending)
New prepared video uses adaptive 80–128px width instead of fixed 48px, with broad compositions reaching the full panel width, extended shot backgrounds and smooth framing changes. No vertical crop; timing/audio unchanged. Converter `device-inspection/prepare-bad-apple-wide.py`, build/visual QA and packaged APK completed. Camera owns the phone lock, so live installation/geometry checks are pending; no competing phone tests/install were performed. Details/preview/install procedure: `device-inspection/outer-animation/BAD-APPLE.md`. Source/assets staged for next build; existing ZIPs unchanged.


## Wider Bad Apple installed and future-release gates — 2026-10-09
Installed the adaptive-width APK with adb install -r and restarted only OuterScreenService. Read-only on-device SHA-256 matches a5c8e0cb3a69c617d6629072f7313387036d1e575ec5c24c206021b3bdebf6bc. Previous data APK retained as device-inspection/outer-animation/OuterScreen-before-wide.apk. The brief application update performed no camera, lid, key, reboot or audio-service operations; camera's phone lock remains untouched. New framing has host render/geometry validation; physical playback geometry checks were not repeated during the camera session. Earlier playback/audio hardware checks apply to unchanged playback code and audio assets.
Future systemimage builds now run the outer-animation/Bad Apple staging script and stock audio PCM ABI fix automatically. Image validation checks embedded wider video/music (including uncompressed m4a), and hashes the packaged outer APK, native display library and tinyalsa against current build outputs. verify-outer-release-assets.py passes for both built and installed APK artifacts; a deliberately stale narrow-media APK is rejected. Bash syntax and Python compilation checks passed. Existing release ZIPs are unchanged; no new ZIP or full system image was built in this update.

## 2026-10-09 — Screen-off timeout and Outer screen settings (built; hardware status below)
Root cause of "never turns off": `visible = lid closed` plus a 5 s re-render alarm, so a closed lid kept the panel lit forever (the old 10 s timeout had been removed). Now the service keeps `litUntil`: the panel is lit while the lid is closed AND (a scene/Bad Apple is playing OR now < litUntil). Lid closing and the side key call `light()`; scene/movie end restarts the timeout; when it expires `refresh()` blanks fb1 once (`FB_BLANK_NORMAL`) and cancels the alarm. A first side press on a dark panel only shows the clock; presses while lit start a scene (if Animations is on); holding 0.8 s starts Bad Apple (if on).
Settings (Settings.Global ints, code defaults, never written by the installer, so they survive reboots/ROM updates; `ContentObserver` applies changes immediately): `kyf37_outer_clock_size` 0/1/2 (def 2), `kyf37_outer_time_format` 0=24h/1=12h (0), `kyf37_outer_seconds` (0), `kyf37_outer_battery` 0 off/1 icon/2 percent/3 both (3), `kyf37_outer_timeout` seconds, 0=always on (10), `kyf37_outer_animation` (1, also hides the idle mascot), `kyf37_outer_badapple` (1). Seconds style re-renders every 1 s while lit. Brightness/contrast: not supported by the fb1 driver (not implemented).
UI: Phone settings row 16 "Outer screen" (`OuterScreenSettings`, up/down select, left/right or OK change, gold focus outline) and Android Settings top-level "Outer screen" entry. Source: `device-inspection/fix-android10-outer-settings.py` (chained at the end of `fix-android10-outer-animation.py`, so every build includes it), `Kyf37OuterScreenSettings.java.txt`; native `kyf37_subdisplay_configure` in render.c, JNI `configure` in controller.c. Installer: `tools/install-outer-settings.ps1`. Build log `~/outer-settings-build.log` (BUILD_EXIT=0, 4m08s).
**Hardware status (honest):** NOT yet installed or verified. APKs are built and staged (`device-inspection/outer-animation/Kyf37OuterScreen-settings.apk`, `Kyf37PhoneSettings-outer.apk`, `Settings-outer.apk`). The phone lock was held by the radio agent until ~15:00, and when this agent acquired it adb showed no device (phone unplugged/off, still absent 45 min later); `tools/install-outer-settings.ps1` therefore aborted before installing anything. To finish: run `tools\install-outer-settings.ps1`, then close the lid with `sendevent /dev/input/event8 5 0 1; sendevent /dev/input/event8 0 0 0` and check that fb1 blanks after the timeout (watch `logcat -s KYF37OuterScreen`, `/sys/class/graphics/fb1/state`), change `settings put global kyf37_outer_clock_size 0` / `kyf37_outer_battery 2` / `kyf37_outer_timeout 5` and confirm `dd if=/dev/graphics/fb1` changes live, then `adb reboot` and re-read `settings list global | grep kyf37_outer`. Whether FB_BLANK_NORMAL physically darkens the panel is also unproven (documented limitation above).
