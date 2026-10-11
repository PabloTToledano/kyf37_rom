#!/bin/bash
# Build + strip + ABI-check the out-of-tree modules against the CURRENT kernel build, and stage them into the vendor tree.
# Run in WSL AFTER the kernel (build-android10-kernel-gcc48.sh). Part of apply-kyf37-kernel-fixes.sh.
set -eo pipefail
D=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection
B=/home/pablo/kyf37-rom/kernel-android10-gcc48-build
STRIP=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-strip
V=/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary/lib/modules
bash $D/build-android10-wlan.sh > /home/pablo/wlanmod.log 2>&1
bash $D/build-android10-core-ctl.sh > /home/pablo/corectl.log 2>&1
W=/home/pablo/kyf37-rom/wlan-prima-caf-123/wlan.ko
C=/home/pablo/kyf37-rom/core-ctl-reference/core_ctl.ko
OUT=/home/pablo/kyf37-rom/kernel-modules-staged; mkdir -p $OUT
$STRIP --strip-debug -o $OUT/pronto_wlan.ko $W
$STRIP --strip-debug -o $OUT/core_ctl.ko $C
python3 $D/check-kernel-module-abi.py $B $OUT/pronto_wlan.ko $OUT/core_ctl.ko
mkdir -p $V/pronto
cp $OUT/pronto_wlan.ko $V/pronto/pronto_wlan.ko
cp $OUT/core_ctl.ko $V/core_ctl.ko
echo "staged into vendor tree: $(ls -l $V/pronto/pronto_wlan.ko $V/core_ctl.ko | awk '{print $5, $9}' | tr '\n' ' ')"
