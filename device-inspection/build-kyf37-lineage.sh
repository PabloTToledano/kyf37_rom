#!/bin/bash
set -eo pipefail
cd /home/pablo/kyf37-lineage
export JAVA_HOME=/home/pablo/kyf37-host-tools/jdk8
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$JAVA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export LC_ALL=C
# Generate model kernel UAPI headers without building/replacing its kernel.
command make -C /home/pablo/kyf37-rom/kernel-source O=/home/pablo/kyf37-rom/kernel-headers-build ARCH=arm HOSTCC="gcc -std=gnu99" INSTALL_HDR_PATH=/home/pablo/kyf37-lineage/out/target/product/kyf37/obj/KERNEL_OBJ/usr headers_install
source build/envsetup.sh
lunch lineage_kyf37-userdebug
command make -j4 bootimage systemimage HOST_CC="gcc -std=gnu99" 2ND_HOST_CC="gcc -std=gnu99" HOST_GLOBAL_ARFLAGS=crsPD 2ND_HOST_GLOBAL_ARFLAGS=crsPD 2>&1 | tee /home/pablo/kyf37-lineage-build.log
