#!/bin/bash
# radio-cell stock-baseline helper. Run from Git Bash with the phone in TWRP (adb state "recovery").
# usage: kycell-swap.sh stock   -> write stock boot (SD kycell/stock-boot.img); system must already be stock (it is, as of 2026-10-09 14:15)
#        kycell-swap.sh a10     -> restore Android 10: system (SD kycell/a10-system.img, used part only) + boot (SD kycell/a10-boot.img)
# Every write is read back and compared. misc is cleared at the end so the next boot is Android. Does not reboot.
# Lesson (2026-10-09): boot writes need clear-recovery-boot-temp-wp FIRST; a plain dd to the boot partition is silently ignored.
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
cd "$(dirname "$0")/.." || exit 1
WHAT=$1
$A devices | grep -q recovery || { echo "phone is not in TWRP"; exit 1; }
$A push device-inspection/clear-recovery-boot-temp-wp /tmp/ >/dev/null
$A push device-inspection/clear-system-temp-wp /tmp/ >/dev/null
$A shell 'chmod 755 /tmp/clear-*-temp-wp'
SD=/external_sd/kycell
case "$WHAT" in
  stock) BOOT=$SD/stock-boot.img; SYS="" ;;
  a10)   BOOT=$SD/a10-boot.img;   SYS=$SD/a10-system.img ;;
  *) echo "usage: $0 stock|a10"; exit 1 ;;
esac
if [ -n "$SYS" ]; then
  $A shell "/tmp/clear-system-temp-wp --clear-system-temporary | tail -1; dd if=$SYS of=/dev/block/mmcblk0p15 bs=4096 2>&1 | tail -1; sync; N=\$(( \$(wc -c < $SYS) / 4096 )); echo SYSTEM_SHA \$(dd if=/dev/block/mmcblk0p15 bs=4096 count=\$N 2>/dev/null | sha256sum); echo EXPECT \$(sha256sum $SYS)"
fi
$A shell "/tmp/clear-recovery-boot-temp-wp --clear-boot-recovery-temporary | tail -1; dd if=$BOOT of=/dev/block/mmcblk0p10 bs=4096 2>&1 | tail -1; sync; echo 3 > /proc/sys/vm/drop_caches; cmp $BOOT /dev/block/mmcblk0p10 && echo BOOT_WRITTEN_OK; dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1 count=80 conv=notrunc 2>/dev/null; sync"
echo "now: $A reboot"
