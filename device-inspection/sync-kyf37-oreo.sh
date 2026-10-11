#!/bin/bash
set -euo pipefail
# Keep the live Nougat bring-up tree intact while evaluating Android 8.1 Go.
mkdir -p /home/pablo/kyf37-oreo
cd /home/pablo/kyf37-oreo
/home/pablo/.local/bin/repo init \
  -u https://github.com/LineageOS/android.git -b lineage-15.1 \
  --depth=1 --git-lfs
/home/pablo/.local/bin/repo sync -c -j4 --no-tags --no-clone-bundle --fail-fast
