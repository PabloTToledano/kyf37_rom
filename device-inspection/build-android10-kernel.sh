#!/bin/bash
set -euo pipefail
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
kernel=/home/pablo/kyf37-rom/kernel-android10
output=/home/pablo/kyf37-rom/kernel-android10-gcc48-build
cross=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-
mkdir -p "$output"
if [ ! -f "$output/.config" ]; then
 cp /home/pablo/kyf37-rom/kernel-oreo-build/.config "$output/.config"
 "$kernel/scripts/config" --file "$output/.config" \
  --enable MEMCG --enable MEMCG_SWAP --enable MEMCG_SWAP_ENABLED \
  --enable CGROUP_DEVICE --enable IKCONFIG_PROC
 make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" olddefconfig
fi
"$kernel/scripts/config" --file "$output/.config" \
 --set-val ARCH_MMAP_RND_BITS 16 --enable CPUSETS --enable BLK_CGROUP \
 --enable TMPFS_XATTR --enable TMPFS_POSIX_ACL --enable FHANDLE
make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" HOSTCC="gcc -std=gnu99 -fcommon" olddefconfig
make -C "$kernel" O="$output" ARCH=arm CROSS_COMPILE="$cross" \
 HOSTCC="gcc -std=gnu99 -fcommon" -j2 zImage modules
