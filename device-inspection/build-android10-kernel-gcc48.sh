#!/bin/bash
set -euo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
src=/home/pablo/kyf37-rom/kernel-android10
out=/home/pablo/kyf37-rom/kernel-android10-gcc48-build
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-
[ "$(git -C "$src" rev-parse HEAD)" = 57a11bec679273e797cbf3fcb3fc1488637b3fe6 ]
mkdir -p "$out"
[ -e "$out/.config" ] || cp /home/pablo/kyf37-rom/kernel-android10-build/.config "$out/.config"
make -C "$src" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" olddefconfig
make -C "$src" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j4 zImage modules
