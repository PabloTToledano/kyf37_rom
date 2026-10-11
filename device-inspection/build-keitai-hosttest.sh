#!/bin/bash
# Build a HOST-TEST variant of the keitai recovery (fake framebuffer -> /fb.raw) and stage a chroot
# for qemu-user. NEVER flash this image. Afterwards rebuild the shipping image with build-keitai-recovery.sh.
set -eo pipefail
HOST=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
python3 $HOST/device-inspection/apply-keitai-recovery.py --hosttest
OUT=/home/pablo/kyf37-twrp/out/target/product/kyf37
rm -rf $OUT/recovery/root/twres
find /home/pablo/kyf37-twrp/out -path '*twrp_intermediates/twrp' -type f -delete 2>/dev/null || true
cd /home/pablo/kyf37-twrp
export JAVA_HOME=/home/pablo/kyf37-host-tools/jdk8
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$JAVA_HOME/bin:$PATH
export LC_ALL=C
source build/envsetup.sh
lunch omni_kyf37-eng
make -j4 recoveryimage TW_KYF37_HOSTTEST=true HOST_CC='gcc -std=gnu99' 2ND_HOST_CC='gcc -std=gnu99' HOST_GLOBAL_ARFLAGS=crsD 2ND_HOST_GLOBAL_ARFLAGS=crsD
T=/home/pablo/kyf37-twrp-hosttest
rm -rf $T && mkdir -p $T
cp -a $OUT/recovery/root $T/root
echo "hosttest root staged in $T/root"
