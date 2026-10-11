#!/bin/bash
set -eo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
kernel=/home/pablo/kyf37-rom/kernel-android10
output=/home/pablo/kyf37-rom/kernel-android10-build
module=/home/pablo/kyf37-rom/core-ctl-reference
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-
make -C "$kernel" O="$output" M="$module" ARCH=arm CROSS_COMPILE="$cross" \
    HOSTCC="gcc -std=gnu99 -fcommon" -j2 modules
