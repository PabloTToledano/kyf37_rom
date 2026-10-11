#!/system/bin/sh
# On-phone helper (Android root shell or TWRP shell). Writes ONE image to the boot or recovery partition with
# hash gates and readback verification. Anything else is refused (never keystore/modem/persist/userdata/misc...).
#   keitai-write-partition.sh <boot|recovery> <image> <image_md5> [<expected_current_md5>|-]
# Prints KEITAI_WRITE_VERIFIED on success. On readback mismatch it exits 3 (caller must restore the backup).
PART="$1"; IMG="$2"; WANT="$3"; CUR="$4"
BLK=/dev/block/bootdevice/by-name
DIR=/data/local/tmp
BB=/sbin/busybox; [ -x $BB ] || BB=""
md5() { $BB md5sum "$1" | $BB cut -d' ' -f1; }
case "$PART" in boot|recovery) ;; *) echo "REFUSED: partition '$PART'"; exit 2;; esac
[ "$($BB id -u)" = 0 ] || { echo "need root"; exit 2; }
SIZE=$($BB stat -c %s "$IMG" 2>/dev/null); [ -z "$SIZE" ] && SIZE=$($BB wc -c < "$IMG")
[ "$SIZE" = 16777216 ] || { echo "image must be 16777216 bytes, is $SIZE"; exit 2; }
[ "$(md5 "$IMG")" = "$WANT" ] || { echo "image md5 mismatch"; exit 2; }
if [ -n "$CUR" ] && [ "$CUR" != "-" ]; then
  now=$(md5 $BLK/$PART)
  [ "$now" = "$CUR" ] || { echo "partition $PART md5 $now is not the expected $CUR; refusing"; exit 2; }
fi
for h in $DIR/clear-recovery-boot-temp-wp /tmp/clear-recovery-boot-temp-wp; do
  [ -x $h ] && { $h --clear-boot-recovery-temporary || exit 2; break; }
done
$BB dd if="$IMG" of=$BLK/$PART bs=4096 2>&1 || exit 3
sync
GOT=$($BB dd if=$BLK/$PART bs=4096 count=4096 2>/dev/null | $BB md5sum | $BB cut -d' ' -f1)
if [ "$GOT" = "$WANT" ]; then echo KEITAI_WRITE_VERIFIED; exit 0; fi
echo "READBACK MISMATCH got=$GOT want=$WANT"; exit 3
