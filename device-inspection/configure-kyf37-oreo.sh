#!/bin/bash
set -e
cd /home/pablo/kyf37-oreo
export JAVA_HOME=/home/pablo/kyf37-oreo/prebuilts/jdk/jdk8/linux-x86
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$JAVA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu
export LC_ALL=C
source build/envsetup.sh
lunch lineage_kyf37-userdebug
get_build_var PLATFORM_VERSION
get_build_var PRODUCT_PROPERTY_OVERRIDES
