#!/bin/bash
# Only invoke through build-locked.sh --staged-ui after a complete staging/build.
# Recompile final UI/policy edits without rerunning older source generators.
set -eo pipefail
flock -n 9 || { echo 'Missing exclusive build-wrapper lock'; exit 1; }
cd /home/pablo/kyf37-android10
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export LC_ALL=C
export BUILD_USERNAME=althia
tail -n 1 /home/pablo/keypad-system-polish-images3.log | grep -qx 'BUILD_EXIT=0' || { echo 'Full image build must pass first'; exit 1; }
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/verify-keypad-system-polish.py
source build/envsetup.sh
lunch lineage_kyf37-userdebug
m -j8 services SystemUI Kyf37Dialer Kyf37Messages Kyf37Contacts systemimage bootimage
