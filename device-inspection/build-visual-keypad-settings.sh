#!/bin/bash
set -eo pipefail
cd /home/pablo/kyf37-android10
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
source build/envsetup.sh
lunch lineage_kyf37-userdebug
m -j8 Kyf37KeypadSettings
