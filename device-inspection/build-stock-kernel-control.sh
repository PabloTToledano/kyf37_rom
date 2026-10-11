#!/bin/bash
set -euo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
src=/home/pablo/kyf37-rom/kernel-source
out=/home/pablo/kyf37-rom/kernel-stock-control-build
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-
[ -z "$(git -C "$src" status --porcelain)" ]
mkdir -p "$out"
[ -e "$out/.config" ] || cp /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/stock-kernel-embedded.config "$out/.config"
make -C "$src" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" olddefconfig
make -C "$src" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j8 zImage
