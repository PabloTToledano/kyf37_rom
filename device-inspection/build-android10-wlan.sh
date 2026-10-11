#!/bin/bash
set -eo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
kernel=/home/pablo/kyf37-rom/kernel-android10
output=/home/pablo/kyf37-rom/kernel-android10-gcc48-build
wlan=/home/pablo/kyf37-rom/wlan-prima-caf-123
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-
make -C "$kernel" O="$output" M="$wlan" ARCH=arm CROSS_COMPILE="$cross" \
    HOSTCC="gcc -std=gnu99 -fcommon" MODNAME=wlan WLAN_ROOT="$wlan" \
    CONFIG_PRONTO_WLAN=m BOARD_PLATFORM=msm8909 -j2 modules
