#!/bin/bash
set -euo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
kernel=/home/pablo/kyf37-rom/kernel-oreo
output=/home/pablo/kyf37-rom/kernel-oreo-build
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-
test -f "$output/.config"
make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" \
 HOSTCC="gcc -std=gnu99 -fcommon" -j2 zImage modules
