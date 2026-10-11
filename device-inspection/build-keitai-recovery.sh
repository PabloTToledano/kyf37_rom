#!/bin/bash
# Re-apply the keitai sources, rebuild the recovery image in ~/kyf37-twrp, copy artifacts
# to kyf37-twrp-device/keitai/. Never touches the phone or the Android 10 tree.
set -eo pipefail
HOST=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
python3 $HOST/device-inspection/apply-keitai-recovery.py
OUT=/home/pablo/kyf37-twrp/out/target/product/kyf37
# make sure no stale stock-theme resources are packed
rm -rf $OUT/recovery/root/twres
find /home/pablo/kyf37-twrp/out -path '*twrp_intermediates/twrp' -type f -delete 2>/dev/null || true
bash $HOST/device-inspection/build-kyf37-twrp.sh
mkdir -p $HOST/kyf37-twrp-device/keitai
cp -f $OUT/recovery.img $HOST/kyf37-twrp-device/keitai/kyf37-keitai-recovery-unsigned.img
cp -rf $OUT/recovery/root/twres $HOST/kyf37-twrp-device/keitai/twres-snapshot
sha256sum $HOST/kyf37-twrp-device/keitai/kyf37-keitai-recovery-unsigned.img
