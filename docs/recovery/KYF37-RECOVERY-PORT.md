# KYF37 recovery port investigation

Status: proposed port; no custom recovery built, booted or flashed.

## Findings

Official TWRP's Kyocera list contains KY41C, not KYF37:
https://twrp.me/Devices/Kyocera/
No verified KYF37 image or device tree was found in the searches performed.
KY41C images must not be treated as compatible.

The Android-5.1 TWRP HardwareKeyboard maps arrows to input-widget keyboard events.
This does not establish usable focus navigation throughout its touch UI:
https://raw.githubusercontent.com/omnirom/android_bootable_recovery/android-5.1/gui/hardwarekeyboard.cpp
https://github.com/TeamWin/Team-Win-Recovery-Project/issues/1485

## Port design

First choice for a full TWRP interface: implement a visible virtual cursor in
gui/gui.cpp. Consume Linux EV_KEY D-pad events before HardwareKeyboard dispatch.
Move the cursor on arrow presses/repeat; center down/up becomes touch start/release;
holding center while pressing arrows generates drag events for sliders and lists.
Render the cursor after the page and before framebuffer flip. Preserve explicit
confirmation sliders; do not turn navigation into automatic confirmation.
This is a proposed implementation, not tested code.

Recorded stock keylayout: up103, down108, left105, right106, center28,
back355. Validate actual getevent reports before binding keys in recovery.
Android input keycodes are different and must not be substituted here.

A text-menu custom recovery is an alternative with simpler key support. AOSP's
Device::HandleMenuKey maps Linux events to highlight/select actions. AOSP recovery
alone does not supply TWRP's backup feature set; these features need a suitable
custom recovery implementation.
https://source.android.com/docs/core/ota/nonab/device_code

## Verified image geometry

Stock recovery was copied and its device/host MD5 matched. Read-only unpacking is
recorded in recovery-stock/inspection.json. Original image remains under
phone-backup/kyf37-root-backup/recovery.img.

- Partition: 16,777,216 bytes; page: 2,048 bytes.
- Kernel: 6,844,280 bytes; device-tree section: 6,531,072 bytes.
- Stock compressed ramdisk: 1,142,337 bytes.
- Kernel load address 0x80008000, ramdisk 0x81000000, tags 0x80000100.
- Keep the exact stock kernel, device-tree section, command line and header layout
  initially; do not substitute another msm8909 device's kernel.
- Large stock device-tree section leaves limited ramdisk space. Check final packed
  image size rather than assuming a typical TWRP ramdisk fits.
- Use extracted recovery fstab as evidence for a branch-specific TWRP fstab;
  stock fstab syntax is not a ready-to-use TWRP fstab.
- Data footer reservation is 16KiB; preserve it when configuring /data.

## Installation dependencies

1. Finish and verify the running full eMMC backup. It is a live image, so mounted
   filesystem consistency is not guaranteed. Keep separate stock boot/recovery,
   aboot and devinfo backups.
2. Establish a verified way for this KYF37 bootloader to accept an unsigned image.
   Current devinfo indicates locked. Diagnostic root and partition write access
   do not prove unsigned recovery can boot. Analyze this phone's aboot before any
   unlock/devinfo changes; generic offsets are insufficient.
3. Build a device-specific recovery in a compatible Linux Android build environment.
   Validate display, keypad, partition paths, size and image packing.
4. If supported, temporarily boot the image before installing it. Availability of
   fastboot boot on KYF37 is not yet established.
5. Only then install and read back recovery, retaining a verified stock restore path.

No flash command is provided because dependencies 1–4 are unresolved. Writing an
unverified image now could leave recovery unusable behind the locked bootloader.
