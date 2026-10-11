#!/bin/bash
set -euo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
kernel=/home/pablo/kyf37-rom/kernel-android10
output=/home/pablo/kyf37-rom/kernel-android10-policy-check
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-
mkdir -p "$output"
cp /home/pablo/kyf37-rom/kernel-android10-build/.config "$output/.config"
make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" olddefconfig
make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j2 prepare scripts
make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" -j2 security/selinux/ security/lsm_audit.o
