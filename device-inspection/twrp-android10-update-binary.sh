#!/sbin/sh
# TWRP update-binary interface: API version, status FD, package pathname.
# This installer never reboots, wipes data, or writes recovery/modem/keystore.
set -eu
BB=/sbin/busybox
BLOCK=/dev/block/bootdevice/by-name
SYSFS=/sys/class/block
MOUNTINFO=/proc/self/mountinfo
SD=/external_sd
OUTFD=${2:?Missing recovery status FD}
ZIP=${3:?Missing package}
WORK=/tmp/kyf37-android10-install-$$
BOOT_HASH=97606038d0450d02c15013b93aa34adece314b956e84e94b04eb2e0ec2533b45
SYSTEM_HASH=155feaec297bf2053415bcc39ff3858c1ec01b98857a10dba8de20e5670540a5
RECOVERY_HASH=9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e
KEYSTORE_HASH=0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c
BOOT_BYTES=16777216
SYSTEM_BYTES=1612709888
WRITING=0
ui() { printf 'ui_print %s\nui_print\n' "$*" >&"$OUTFD"; }
die() { ui "ERROR: $*"; exit 1; }
finish() {
    result=$?
    trap - EXIT
    if [ "$result" != 0 ]; then
        ui 'Installation failed. Stay in TWRP; do not reboot the candidate.'
        [ "$WRITING" = 0 ] || ui "Restore boot/system from $BACKUP or the verified stock backup."
    fi
    [ ! -d "$WORK" ] || "$BB" rm -rf "$WORK"
    exit "$result"
}
trap finish EXIT
[ -x "$BB" ] || die 'Recovery busybox is missing.'
[ "$($BB id -u)" = 0 ] || die 'Root recovery is required.'
[ "$(getprop ro.product.model)" = KYF37 ] || die 'This ZIP is only for KYF37.'
[ "$(getprop ro.serialno)" = 981108631314 ] || die 'This owner-signed ZIP is for serial 981108631314.'
[ "$(getprop ro.twrp.version)" = 3.7.0_9-0 ] || die 'Use the verified KYF37 TWRP 3.7.0_9-0.'
case "$OUTFD" in ''|*[!0-9]*) die 'Invalid recovery status FD.';; esac
case "$ZIP" in /system/*|/system_root/*) die 'Move the ZIP onto microSD before installing.';; esac
[ -f "$ZIP" ] || die 'Installer ZIP cannot be read.'
ui 'KYF37 Android 10 Go experimental candidate'
ui 'Hardware boot and VoLTE remain unverified. Userdata will be preserved.'
hash() { value=$($BB sha256sum "$1") || return 1; printf '%s\n' "${value%% *}"; }
check() { [ "$(hash "$1")" = "$2" ] || die "SHA256 mismatch: $1"; }
for part in boot system recovery keystore; do
    [ -b "$BLOCK/$part" ] || die "Missing block partition: $part"
done
[ "$($BB readlink -f "$BLOCK/boot")" = /dev/block/mmcblk0p10 ] || die 'Boot partition differs.'
[ "$($BB readlink -f "$BLOCK/system")" = /dev/block/mmcblk0p15 ] || die 'System partition differs.'
[ "$($BB blockdev --getsize64 "$BLOCK/boot")" = "$BOOT_BYTES" ] || die 'Boot size differs.'
[ "$($BB blockdev --getsize64 "$BLOCK/system")" = "$SYSTEM_BYTES" ] || die 'System size differs.'
[ "$($BB cat "$SYSFS/mmcblk0p10/start")" = 151552 ] || die 'Boot start sector differs.'
[ "$($BB cat "$SYSFS/mmcblk0p15/start")" = 290816 ] || die 'System start sector differs.'
check "$BLOCK/recovery" "$RECOVERY_HASH"
check "$BLOCK/keystore" "$KEYSTORE_HASH"
ui 'Checking complete payload hashes before any partition changes...'
payload_hash() {
    value=$($BB unzip -p "$ZIP" "$1" | "$BB" sha256sum) || return 1
    printf '%s\n' "${value%% *}"
}
[ "$(payload_hash boot.img)" = "$BOOT_HASH" ] || die 'Signed boot payload is damaged.'
[ "$(payload_hash system.raw.img)" = "$SYSTEM_HASH" ] || die 'System payload is damaged.'
"$BB" mkdir "$WORK"
"$BB" unzip -p "$ZIP" tools/clear-system-temp-wp > "$WORK/clear-system-temp-wp"
"$BB" unzip -p "$ZIP" tools/clear-recovery-boot-temp-wp > "$WORK/clear-recovery-boot-temp-wp"
check "$WORK/clear-system-temp-wp" @SYSTEM_WP_SHA@
check "$WORK/clear-recovery-boot-temp-wp" @BOOT_WP_SHA@
"$BB" chmod 0755 "$WORK/clear-system-temp-wp" "$WORK/clear-recovery-boot-temp-wp"
"$BB" mountpoint -q "$SD" || die 'Mount the microSD at /external_sd in TWRP first.'
# Require external card storage, not an alias of internal userdata.
sd_external=0
while read src target rest; do
    if [ "$target" = "$SD" ]; then
        real=$($BB readlink -f "$src")
        case "$real" in /dev/block/mmcblk1|/dev/block/mmcblk1p*) sd_external=1;; esac
    fi
done < /proc/mounts
[ "$sd_external" = 1 ] || die 'Backup path is not the external microSD.'
free=$($BB df -Pk "$SD" | "$BB" awk 'NR==2 {print $4}')
case "$free" in ''|*[!0-9]*) die 'Cannot determine microSD free space.';; esac
[ "$free" -ge 1700000 ] || die 'MicroSD needs at least 1.7 GB free for rollback images.'
case "${4:-}" in
    --check-only) ui 'Preflight passed. Check-only: no backup, unmount or device writes.'; exit 0;;
    ''|retry) ;;
    *) die 'Unknown installer argument.';;
esac
if "$BB" mountpoint -q /system; then "$BB" umount /system || die 'Cannot unmount /system.'; fi
# Check kernel mount device IDs, including aliases and bind mounts.
boot_dev=$($BB cat "$SYSFS/mmcblk0p10/dev")
system_dev=$($BB cat "$SYSFS/mmcblk0p15/dev")
while read mount_id parent device rest; do
    [ "$device" != "$boot_dev" ] && [ "$device" != "$system_dev" ] || die 'Boot/system is still mounted.'
done < "$MOUNTINFO"
BACKUP=$SD/KYF37-Android10-rollback-$($BB date +%Y%m%d-%H%M%S)-$$
"$BB" mkdir "$BACKUP" || die 'Cannot create rollback directory.'
ui "Saving rollback images to $BACKUP ..."
for part in boot system; do
    before=$(hash "$BLOCK/$part") || die "Cannot read current $part."
    "$BB" dd if="$BLOCK/$part" of="$BACKUP/$part.img" bs=1048576 || die "Backup of $part failed."
    check "$BACKUP/$part.img" "$before"
    printf '%s  %s.img\n' "$before" "$part" >> "$BACKUP/SHA256SUMS"
done
"$BB" sync
# Record unchanged protected/radio partition hashes without modifying them.
for part in recovery keystore modem modemst1 modemst2 fsg persist; do
    if [ -b "$BLOCK/$part" ]; then
        preserved=$(hash "$BLOCK/$part") || die "Cannot hash preserved partition $part."
        printf '%s %s\n' "$preserved" "$part" >> "$WORK/preserved.sha256"
    fi
done
"$BB" cp "$WORK/preserved.sha256" "$BACKUP/preserved.sha256"
ui 'Clearing only temporary eMMC write protection for the verified ranges...'
# eMMC protection groups overlap recovery; this changes protection, not recovery contents.
"$WORK/clear-system-temp-wp" --clear-system-temporary || die 'System temporary write-protection check failed.'
"$WORK/clear-recovery-boot-temp-wp" --clear-boot-recovery-temporary || die 'Boot temporary write-protection check failed.'
WRITING=1
ui 'Writing system image...'
"$BB" unzip -p "$ZIP" system.raw.img | "$BB" dd of="$BLOCK/system" bs=1048576 || die 'System write failed.'
"$BB" sync
check "$BLOCK/system" "$SYSTEM_HASH"
ui 'Writing owner-signed boot image...'
"$BB" unzip -p "$ZIP" boot.img | "$BB" dd of="$BLOCK/boot" bs=4096 || die 'Boot write failed.'
"$BB" sync
check "$BLOCK/boot" "$BOOT_HASH"
while read expected part; do check "$BLOCK/$part" "$expected"; done < "$WORK/preserved.sha256"
ui 'Boot/system readback verified; recovery, keystore and recorded modem partitions unchanged.'
ui "Rollback images: $BACKUP"
ui 'Install complete. No automatic reboot. First boot is a hardware test; retain this backup.'
printf 'set_progress 1.0\n' >&"$OUTFD"
exit 0
