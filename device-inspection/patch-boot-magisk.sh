#!/bin/bash
# Patch a KYF37 legacy boot image with Magisk v23 (run in WSL). usage: patch-boot-magisk.sh <in-unsigned.img> <out-unsigned.img>
# Same ramdisk edits as Magisk's boot_patch.sh for a 32-bit, non-system-as-root device (no magisk64, no 64-bit kernel hex patches).
# The result still has to be owner-signed (sign-rom-boot.py). Idempotent: an already patched input is re-patched from its backup.
set -e
IN=$(readlink -f "$1"); OUT=$(readlink -f -m "$2")
D=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection
W=$(mktemp -d ~/magiskpatch.XXXXXX); trap 'rm -rf $W' EXIT; cd $W
cp $D/magisk23/x86/libmagiskboot.so magiskboot; cp $D/magisk23/libmagiskinit.so magiskinit; cp $D/magisk23/libmagisk32.so magisk32
chmod +x magiskboot magiskinit magisk32
cp "$IN" boot.img
./magiskboot unpack boot.img >/dev/null
./magiskboot cpio ramdisk.cpio test; STATUS=$?
case $((STATUS & 3)) in
  0) SHA1=$(./magiskboot sha1 boot.img); cp -af ramdisk.cpio ramdisk.cpio.orig ;;
  1) SHA1=$(./magiskboot cpio ramdisk.cpio sha1 2>/dev/null); ./magiskboot cpio ramdisk.cpio restore; cp -af ramdisk.cpio ramdisk.cpio.orig ;;
  *) echo "unsupported ramdisk status $STATUS"; exit 1 ;;
esac
printf 'KEEPVERITY=false\nKEEPFORCEENCRYPT=false\nRECOVERYMODE=false\nSHA1=%s\n' "$SHA1" > config
./magiskboot compress=xz magisk32 magisk32.xz
./magiskboot cpio ramdisk.cpio \
  "add 0750 init magiskinit" \
  "mkdir 0750 overlay.d" \
  "mkdir 0750 overlay.d/sbin" \
  "add 0644 overlay.d/sbin/magisk32.xz magisk32.xz" \
  "patch" \
  "backup ramdisk.cpio.orig" \
  "mkdir 000 .backup" \
  "add 000 .backup/.magisk config"
for dt in dtb kernel_dtb extra; do [ -f $dt ] && ./magiskboot dtb $dt patch; done || true
./magiskboot repack boot.img new-boot.img >/dev/null
SZ=$(stat -c %s new-boot.img)
# keep the partition-sized image the bootloader expects
[ $SZ -le 16777216 ] || { echo "patched image too large: $SZ"; exit 1; }
cp new-boot.img "$OUT"
echo "magisk-patched boot: $OUT ($SZ bytes) sha1(stock)=$SHA1"
