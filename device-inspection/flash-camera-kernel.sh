#!/bin/bash
# Swap kernel into v17 boot, sign, flash via TWRP, reboot, start camera daemon. Run from repo root in Git Bash.
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe; R=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
# Modules must match this exact kernel or Wi-Fi/core_ctl will not load (module_layout CRC); rebuild + ABI-check them first.
wsl -d Ubuntu -- bash $R/device-inspection/build-kyf37-modules.sh | tail -4 || exit 1
mkdir -p kyf37-rom/modules-staged; wsl -d Ubuntu -- bash -c "cp ~/kyf37-rom/kernel-modules-staged/*.ko $R/kyf37-rom/modules-staged/"
rm -f kyf37-rom/boot-camerafix-*.img
wsl -d Ubuntu -- python3 $R/device-inspection/make-camera-kernel-boot.py $R/kyf37-rom/android10-go-candidate-20261007-v17/boot-android10-unsigned.img /home/pablo/kyf37-rom/kernel-android10-gcc48-build/arch/arm/boot/zImage $R/kyf37-rom/boot-camerafix-unsigned.img
python device-inspection/sign-rom-boot.py kyf37-rom/boot-camerafix-unsigned.img kyf37-rom/boot-camerafix-signed.img >/dev/null 2>&1 || exit 1
$A root >/dev/null; sleep 4
$A shell 'printf "boot-recovery\000" | dd of=/dev/block/bootdevice/by-name/misc bs=1 count=14 conv=notrunc 2>/dev/null; printf "recovery\n" | dd of=/dev/block/bootdevice/by-name/misc bs=1 seek=64 count=9 conv=notrunc 2>/dev/null; sync; reboot'
for i in $(seq 1 50); do sleep 5; $A devices | grep -q recovery && break; done
$A push device-inspection/clear-recovery-boot-temp-wp /tmp/ >/dev/null; $A push kyf37-rom/boot-camerafix-signed.img /tmp/ >/dev/null
$A shell "chmod 755 /tmp/clear-recovery-boot-temp-wp; /tmp/clear-recovery-boot-temp-wp --clear-boot-recovery-temporary | tail -1; dd if=/tmp/boot-camerafix-signed.img of=/dev/block/mmcblk0p10 bs=4096 2>/dev/null; sync; cmp /tmp/boot-camerafix-signed.img /dev/block/mmcblk0p10 && echo BOOT_OK; dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1 count=80 conv=notrunc 2>/dev/null; sync"
$A reboot
for i in $(seq 1 90); do sleep 6; [ "$($A shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && break; done
$A root >/dev/null; sleep 4

sleep 30; $A root >/dev/null; sleep 3; $A shell "uname -v; ps -A | grep -E 'qcamera|lkspad'"
# install the matching modules on the phone (survives reboot: /system write-protect cleared first)
$A push kyf37-rom/modules-staged/pronto_wlan.ko /data/local/tmp/pronto_wlan.ko >/dev/null; $A push kyf37-rom/modules-staged/core_ctl.ko /data/local/tmp/core_ctl.ko >/dev/null
$A push device-inspection/clear-system-temp-wp /data/local/tmp/ >/dev/null
$A shell "chmod 755 /data/local/tmp/clear-system-temp-wp; /data/local/tmp/clear-system-temp-wp --clear-system-temporary | tail -1; mount -o remount,rw /system; cp /data/local/tmp/pronto_wlan.ko /system/lib/modules/pronto/pronto_wlan.ko; cp /data/local/tmp/core_ctl.ko /system/lib/modules/core_ctl.ko; sync; mount -o remount,ro /system; insmod /system/lib/modules/core_ctl.ko 2>&1 | head -1; svc wifi disable; sleep 2; svc wifi enable; sleep 12; ip addr show wlan0 | head -3"
