#!/system/bin/sh
set -eu
BB=/data/local/tmp/busybox
DIR=/data/local/tmp
BLOCK=/dev/block/bootdevice/by-name
check() {
    actual=$($BB md5sum "$1");actual=${actual%% *}
    [ "$actual" = "$2" ] || { echo "Hash mismatch: $1 actual=$actual"; return 1; }
}
[ "$($BB id -u)" = 0 ]
[ "$(getprop ro.product.model)" = KYF37 ]
check "$BLOCK/boot" 03f4157ba5b1e15dfa8e53e10209f926
check "$BLOCK/keystore" 3393e25f2fb2959a2d0a8e9bea495ac5
check "$BLOCK/recovery" d74f99b6038d266e838c6ed0311eaa1b
check "$DIR/stock-recovery-owner-signed.img" d74f99b6038d266e838c6ed0311eaa1b
check "$DIR/kyf37-twrp-owner-signed.img" 6747701ad2be0ecd50d76f4e9744aaae
"$DIR/clear-recovery-boot-temp-wp" --clear-boot-recovery-temporary
rollback() {
    result=$?;trap - EXIT INT TERM
    if [ "$result" != 0 ]; then
        set +e
        echo 'Recovery write failed; restoring owner-signed stock recovery.'
        $BB dd if="$DIR/stock-recovery-owner-signed.img" of="$BLOCK/recovery" bs=4096
        sync
        check "$BLOCK/recovery" d74f99b6038d266e838c6ed0311eaa1b
    fi
    exit "$result"
}
trap rollback EXIT
trap 'exit 130' INT TERM
$BB dd if="$DIR/kyf37-twrp-owner-signed.img" of="$BLOCK/recovery" bs=4096
sync
check "$BLOCK/recovery" 6747701ad2be0ecd50d76f4e9744aaae
echo KYF37_TWRP_FLASH_READBACK_VERIFIED
trap - EXIT INT TERM
