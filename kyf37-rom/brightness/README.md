# KYF37 brightness control — 2026-10-10

## Correction after owner test (later findings supersede earlier results)

The owner reported no visible change from Settings after the first installation.
Settings and generic lcd-backlight both read 10, but `backlightinfo` still read
79. The previous generic-node readbacks did **not** establish actual luminance
control; the initial completion claim was premature.

Kernel device-tree `msm8909-mtp.dtsi` maps LV5216 `lcd_backlight`/`mled` to
`backlightinfo`. `lv5216_ctrl_mled` in `drivers/leds/leds-lv5216kc.c` writes
the controller's current/enable registers for manual levels. The generic MDP
node is separate. Direct backlightinfo requests 20 and 200 returned both
brightness and sensor_brightness 20/200; the latter is updated by the MLED
work function that programs the hardware (not an optical measurement).

The corrected HAL writes both generic LCD and actual LV5216 MLED nodes for
BACKLIGHT only. Button-backlight behavior is unchanged. This source lives in
the same replayable template/staging pipeline and inherits the release hash
gate. Build log for this correction: `/home/pablo/brightness-build-4.log`.

## Finding

The running ROM exposes manual brightness settings, but setting 40 and 200
both left `/sys/class/leds/lcd-backlight/brightness` at 255 (`before.txt`).
Android display state reported the requested values. The light HIDL service
was running, but its process maps contained no legacy lights HAL. The phone
had no `lights.kyf37.so` and the build output also lacked it, despite
`ro.hardware.lights=kyf37` and PRODUCT_PACKAGES selecting that module.

The existing module was declared as a system module. The vendor light HIDL
implementation uses vendor libhardware, whose `__ANDROID_VNDK__` loader
searches ODM/vendor, excluding `/system/lib/hw`. The unrelated stock
`kc_lights.default.so` is not a replacement for the standard lights module.

## Reproducible correction

`device-inspection/fix-android10-brightness.py` stages the existing driver,
declares `LOCAL_VENDOR_MODULE := true`, and ensures product selection and
the hardware property. The build wrapper runs it before lunch. The image
validator now requires `/vendor/lib/hw/lights.kyf37.so` in the raw system
image and compares its hash with the current build output. Existing ZIPs
are unchanged; the next freshly built and validated ZIP includes this fix.

Build through `device-inspection/build-locked.sh <log> lights.kyf37`.
The driver writes the standard 0–255 brightness to the evidenced LCD node;
the kernel advertises max_brightness=255. No kernel/framework change needed.

## Live installation and rollback

`tools/install-brightness.ps1` installs the provided `lights.kyf37.so`,
clears temporary system write protection, restores permissions/context,
syncs and remounts system read-only, then restarts only
`vendor.light-hal-2-0`. It uses the cooperative phone lock. No image flash.
The original file, if any, is saved under
`/data/local/tmp/brightness-rollback/`; `originally-absent` records this
phone's baseline. Roll back while holding the lock: clear temporary write
protection, remount system rw, restore the backup (or remove only the new
`/vendor/lib/hw/lights.kyf37.so` if originally absent), sync, remount ro,
and restart the same light service. This restores the old broken brightness.

Auto brightness remains unsupported: this change restores manual control.

The first targeted build failed with `unknown target 'lights.kyf37'`.
This exposed the primary omission: the top-level device Android.mk had no
include for lights/Android.mk (and does not recurse automatically). The fix
script now adds that explicit include as well as the vendor declaration.
Build logs: `/home/pablo/brightness-build.log` (failed discovery) and
`/home/pablo/brightness-build-2.log` (corrected build).

The second build reached compilation and exposed an invalid pre-existing
constant `LIGHTS_MODULE_API_VERSION_1_0` (not defined in Android 10 headers).
Replaced it with `HARDWARE_MODULE_API_VERSION(1, 0)` in the host template;
the staging script replays that source correction. Final build log:
`/home/pablo/brightness-build-3.log`.

## Verified live result

Final targeted build succeeded (51 seconds, BUILD_EXIT=0). Installed library
SHA-256: `f19a3c1f13404137d3707ca9ced01f6e8ec3d50b1a93ba93a72e8b912d9213d0`.
The on-device hash matches. Only the light HIDL service was restarted;
the new driver is visible in that service's process maps. No reboot/flash.

Android settings requests 40, 120, 200 produced kernel backlight values
40, 120, 200, respectively (`after.txt`). Original manual setting 32 and
mode 0 restored. Android sleep/wake keys produced 0 with screen off and
32 after wake (`wake-check.txt`). System mounted read-only, boot_completed=1,
uptime 1407 seconds; no recent matching light errors/FATAL EXCEPTION.
Phone lock released. These are hardware backlight-driver readbacks;
no human visual judgement of luminance or slider/keypad usability claimed.
Reboot persistence and a newly packaged full ZIP were not tested here.

Future reproduction: run the staging script, then the normal locked
systemimage/build/release pipeline. The full image validator's new hash
gate has been added but not executed against a new image in this task.

Corrected MLED build passed (BUILD_EXIT=0, 63 s) and installed without flash/reboot.
SHA-256: 5f0a0e487197f3fb1d49c99fdb0c3af4c068afa397398b301f1245aea47a62a5.
Android settings requests 40 and 200 now returned 40/40/40 and 200/200/200
for generic LCD, MLED brightness, and MLED applied sensor_brightness.
Restored owner's current setting 10. Sleep returned MLED 0/0, wake 10/10.
System read-only, phone lock released. See after-mled.txt and wake-mled.txt.
Physical visual confirmation by the owner is still needed; no optical measurement.
This correction supersedes the generic-node-only result and library hash below.
