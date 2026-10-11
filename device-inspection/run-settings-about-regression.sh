#!/bin/bash
set -eo pipefail
cd /home/pablo/kyf37-android10
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export LC_ALL=C
export MKE2FS_CONFIG=/home/pablo/kyf37-android10/system/extras/ext4_utils/mke2fs.conf
mkdir -p /home/pablo/kyf37-rom/kernel-android10-headers
command make -C /home/pablo/kyf37-rom/kernel-android10 O=/home/pablo/kyf37-rom/kernel-android10-headers ARCH=arm HOSTCC="gcc -std=gnu99 -fcommon" INSTALL_HDR_PATH=/home/pablo/kyf37-android10/out/target/product/kyf37/obj/KERNEL_OBJ/usr headers_install
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/filter-android10-kernel-headers.py /home/pablo/kyf37-android10/out/target/product/kyf37/obj/KERNEL_OBJ/usr/include
source build/envsetup.sh
lunch lineage_kyf37-userdebug
export ROBOTEST_FILTER=WifiMacAddressPreferenceControllerTest
export ROBOTEST_FAILURE_FATAL=true
m -j8 RunSettingsLibRoboTests
