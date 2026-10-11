#!/bin/bash
set -euo pipefail
root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research
work=/home/pablo/kyf37-kernel-port-research/backports
kernel=$work/kernel
out=$work/build
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
export LOCALVERSION=
python3 "$root/backport-working-kernel.py"
"$kernel/scripts/config" --file "$out/.config" --enable ZRAM --enable ZSMALLOC --enable ZRAM_LZ4_COMPRESS --enable LZ4_COMPRESS --enable LZ4_DECOMPRESS --disable LOCALVERSION_AUTO --set-str LOCALVERSION ""
make -C "$kernel" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" olddefconfig
make -C "$kernel" O="$out" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j4 zImage modules
make -C "$kernel" O="$out" M="$work/core-ctl" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j2 modules
make -C "$kernel" O="$out" M="$work/wlan" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" MODNAME=wlan WLAN_ROOT="$work/wlan" CONFIG_PRONTO_WLAN=m BOARD_PLATFORM=msm8909 -j2 modules
echo 'BACKPORT KERNEL AND MODULE BUILDS COMPLETE; NO DEVICE ACCESS.'
