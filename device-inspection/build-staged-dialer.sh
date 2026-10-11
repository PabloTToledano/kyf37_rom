#!/bin/bash
# App-only rebuild from the validated v23 source set, always under build-locked.sh.
set -eo pipefail
flock -n 9 || { echo 'Missing exclusive build-wrapper lock'; exit 1; }
tail -n 1 /home/pablo/v23-keypad-release-build.log | grep -qx 'BUILD_EXIT=0'
cd /home/pablo/kyf37-android10
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export LC_ALL=C BUILD_USERNAME=althia
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-dialer-lid-close.py
source build/envsetup.sh
lunch lineage_kyf37-userdebug
m -j8 Kyf37Dialer
