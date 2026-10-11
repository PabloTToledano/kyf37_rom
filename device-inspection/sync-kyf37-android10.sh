#!/bin/bash
set -euo pipefail
mkdir -p /home/pablo/kyf37-android10
cd /home/pablo/kyf37-android10
/home/pablo/.local/bin/repo init -u https://github.com/LineageOS/android.git \
  -b lineage-17.1 --depth=1 --manifest-depth=1 --git-lfs
/home/pablo/.local/bin/repo sync -c -j4 --no-tags --no-clone-bundle --fail-fast
