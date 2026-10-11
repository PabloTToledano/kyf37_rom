#!/bin/bash
# usage: package-release.sh vN   (run in WSL after a successful build)  -> prints steps; signing/zip done on Windows side
set -eo pipefail
N=$1; D=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection; R=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom
cd ~
# GATE: kernel modules must match the kernel they ship with (a mismatch silently kills Wi-Fi: 'disagrees about version of symbol module_layout')
cmp -s /home/pablo/kyf37-rom/kernel-android10-gcc48-build/arch/arm/boot/zImage /home/pablo/kyf37-android10/device/kyocera/kyf37/kernel || { echo 'ABORT: device/kyocera/kyf37/kernel is not the kernel in kernel-android10-gcc48-build; run apply-kyf37-kernel-fixes.sh'; exit 1; }
python3 $D/check-kernel-module-abi.py /home/pablo/kyf37-rom/kernel-android10-gcc48-build /home/pablo/kyf37-android10/out/target/product/kyf37/system/lib/modules/pronto/pronto_wlan.ko /home/pablo/kyf37-android10/out/target/product/kyf37/system/lib/modules/core_ctl.ko || { echo 'ABORT: kernel modules do not match the kernel; run build-kyf37-modules.sh and rebuild the system image'; exit 1; }
python3 $D/package-android10-legacy-boot.py --release --output /home/pablo/kyf37-rom/boot-$N-release-unsigned.img | grep sha256
python3 $D/validate-android10-images.py --boot /home/pablo/kyf37-rom/boot-$N-release-unsigned.img --raw-output /home/pablo/kyf37-rom/system-$N.raw.img | grep filesystem_check_exit
python3 $D/audit-installed-vendor-symbols.py --tree /home/pablo/kyf37-android10 --report $R/android10-installed-vendor-symbol-audit-$N.json --label $N
python3 $D/stage-v10-candidate.py $N /home/pablo/kyf37-rom/boot-$N-release-unsigned.img /home/pablo/kyf37-rom/system-$N.raw.img
cp /home/pablo/kyf37-android10/external/boringssl/src/LICENSE $R/android10-go-candidate-20261007-$N/BoringSSL-LICENSE.txt
# GATE: refuse to release an image that contains boot-breaking leftovers or lacks required pieces (see check-release-image.py)
python3 $D/check-release-image.py $R/android10-go-candidate-20261007-$N/system-android10.raw.img || { echo "ABORT: release image gate failed - do not flash"; exit 1; }
