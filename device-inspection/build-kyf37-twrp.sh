#!/bin/bash
set -eo pipefail
cd /home/pablo/kyf37-twrp
export JAVA_HOME=/home/pablo/kyf37-host-tools/jdk8
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$JAVA_HOME/bin:$PATH
export LC_ALL=C
source build/envsetup.sh
lunch omni_kyf37-eng
make -j4 recoveryimage HOST_CC='gcc -std=gnu99' 2ND_HOST_CC='gcc -std=gnu99' HOST_GLOBAL_ARFLAGS=crsD 2ND_HOST_GLOBAL_ARFLAGS=crsD
