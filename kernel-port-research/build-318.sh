#!/bin/bash
# Isolated experimental build. Never stages into the existing Android ROM.
set -euo pipefail
root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research
work=/home/pablo/kyf37-kernel-port-research
src=$work/kernel-3.18
out=$work/build-3.18
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
mkdir -p "$out"
python3 "$root/prepare-kyf37-318.py"
make -C "$src" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" KYF37_port_defconfig
make -C "$src" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j4 zImage modules dtbs
sha256sum "$out/arch/arm/boot/zImage" > "$root/logs/zImage.sha256"
cp "$out/.config" "$root/compiled-318.config"
echo 'COMPILE COMPLETE: hardware compatibility NOT verified; no images staged or flashed.'
