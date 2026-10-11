#!/sbin/sh
# Exact checked test candidate. Run only in the already-installed TWRP.
set -eu
BB=/sbin/busybox
BLOCK=/dev/block/bootdevice/by-name
STAGE=/data/local/tmp/kyf37-rom-20261007
RAW=/external_sd/kyf37-rom-20261007/system.raw.img
BACKUP=/external_sd/TWRP/BACKUPS/981108631314/kyf37-pre-lineage-20261007
check() {
    actual=$($BB sha256sum "$1");actual=${actual%% *}
    [ "$actual" = "$2" ] || { echo "Hash mismatch: $1 $actual"; exit 1; }
}
[ "$($BB id -u)" = 0 ]
[ "$(getprop ro.product.model)" = KYF37 ]
[ "$(getprop ro.twrp.version)" = 3.7.0_9-0 ]
[ "$($BB readlink -f "$BLOCK/system")" = /dev/block/mmcblk0p15 ]
[ "$($BB readlink -f "$BLOCK/boot")" = /dev/block/mmcblk0p10 ]
[ "$($BB blockdev --getsize64 "$BLOCK/system")" = 1612709888 ]
[ "$($BB blockdev --getsize64 "$BLOCK/boot")" = 16777216 ]
set -- $($BB stat -t "$RAW")
[ "$2" = 1612709888 ]
[ -f "$BACKUP/boot.emmc.win.md5" ]
[ -f "$BACKUP/system.ext4.win.md5" ]
found_data=0
for digest in "$BACKUP"/data.ext4.win*.md5; do
    [ -f "$digest" ] && found_data=1
done
[ "$found_data" = 1 ]
for digest in "$BACKUP"/*.md5; do
    (cd "$BACKUP"; "$BB" md5sum -c "$($BB basename "$digest")")
done
check "$RAW" 7e2dae04dc3b75e69614ebdc78def0398c287f37cc334772b529fc476595e21b
check "$STAGE/boot-lineage-owner-signed.img" 84b5e7e7ee82bfdc9bb6f31a07a3ca970bcdd670412d69595e220b3a4a9724c3
check "$BLOCK/boot" 466fd5ead33dabb54446ecf2f2132edc821e8d7da0c2f5d9f61fb08c45bcc3ed
check "$BLOCK/recovery" 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e
check "$BLOCK/keystore" 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c
# Finish backup mounts before any block write; leave data and microSD mounted.
if "$BB" mountpoint -q /system; then "$BB" umount /system; fi
while read source target rest; do
    [ "$source" != /dev/block/mmcblk0p15 ] || { echo 'System remains mounted'; exit 1; }
done < /proc/mounts
"$STAGE/../clear-system-temp-wp" --clear-system-temporary
"$STAGE/../clear-recovery-boot-temp-wp" --clear-boot-recovery-temporary
# On failure stay in recovery for restoration; never reboot automatically.
trap 'echo ROM_WRITE_FAILED_STAY_IN_TWRP' EXIT
"$BB" dd if="$RAW" of="$BLOCK/system" bs=1048576
sync
check "$BLOCK/system" 7e2dae04dc3b75e69614ebdc78def0398c287f37cc334772b529fc476595e21b
"$BB" dd if="$STAGE/boot-lineage-owner-signed.img" of="$BLOCK/boot" bs=4096
sync
check "$BLOCK/boot" 84b5e7e7ee82bfdc9bb6f31a07a3ca970bcdd670412d69595e220b3a4a9724c3
check "$BLOCK/recovery" 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e
check "$BLOCK/keystore" 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c
trap - EXIT
echo KYF37_LINEAGE_BOOT_SYSTEM_READBACK_VERIFIED
