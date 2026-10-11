#!/bin/bash
# Owner-sign and flash a legacy boot image through TWRP (misc BCB route), reboot, wait for Android. Run from the repo root in Git Bash.
# usage: flash-boot-image.sh <unsigned-boot.img> <signed-output.img>
# Rollback: flash the previous signed image the same way (kyf37-rom/boot-camerafix-signed.img is the last known-good).
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
IN=$1; OUT=$2
python device-inspection/sign-rom-boot.py "$IN" "$OUT" >/dev/null 2>&1 || { echo "signing failed"; exit 1; }
$A root >/dev/null; sleep 3
$A shell 'printf "boot-recovery\000" | dd of=/dev/block/bootdevice/by-name/misc bs=1 count=14 conv=notrunc 2>/dev/null; printf "recovery\n" | dd of=/dev/block/bootdevice/by-name/misc bs=1 seek=64 count=9 conv=notrunc 2>/dev/null; sync; reboot'
for i in $(seq 1 50); do sleep 5; $A devices | grep -q recovery && break; done
$A devices | grep -q recovery || { echo "phone did not reach TWRP"; exit 1; }
$A push device-inspection/clear-recovery-boot-temp-wp /tmp/ >/dev/null; $A push "$OUT" /tmp/boot-new.img >/dev/null
SUM=$(sha256sum "$OUT" | cut -d' ' -f1)
$A shell "chmod 755 /tmp/clear-recovery-boot-temp-wp; /tmp/clear-recovery-boot-temp-wp --clear-boot-recovery-temporary | tail -1; dd if=/tmp/boot-new.img of=/dev/block/mmcblk0p10 bs=4096 2>/dev/null; sync; cmp /tmp/boot-new.img /dev/block/mmcblk0p10 && echo BOOT_OK; dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1 count=80 conv=notrunc 2>/dev/null; sync"
$A reboot
for i in $(seq 1 90); do sleep 6; [ "$($A shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && { echo "ANDROID UP after flash of $SUM"; exit 0; }; done
echo "Android did not complete boot within ~9 minutes"; exit 2
