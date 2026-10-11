#!/bin/bash
# Re-apply every KYF37 kernel change (idempotent) in the right order, then build the kernel. Run in WSL:
#   wsl -d Ubuntu -- bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/apply-kyf37-kernel-fixes.sh
# Sources of third-party code: third-party/sdcardfs/README.md (fs/sdcardfs must be fetched into ~/third-party-sdcardfs first).
set -e
D=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection
for s in \
  fix-android10-camera-session-fallback.py fix-android10-camera-session-fallback2.py fix-android10-camera-notify-id.py \
  fix-android10-camera-notify-cmd.py fix-android10-camera-notify-status.py fix-android10-camera-drop-bogus-notify.py \
  fix-android10-kernel-sdcardfs.py fix-android10-kernel-sdcardfs-vfs.py fix-android10-kernel-sdcardfs-remount.py \
  fix-android10-kernel-memfd.py fix-android10-kernel-ambient-light.py ; do
  echo "== $s"; python3 $D/$s
done
# camera userspace + ramdisk/vendor integration (also copies the built zImage into device/kyocera/kyf37/kernel)
bash $D/build-android10-kernel-gcc48.sh > ~/kbuild.log 2>&1 && echo "kernel built: $(ls -l ~/kyf37-rom/kernel-android10-gcc48-build/arch/arm/boot/zImage)"
# out-of-tree modules (wlan, core_ctl) MUST be rebuilt for every kernel build (module_layout CRC changes) and are ABI-checked
bash $D/build-kyf37-modules.sh
for s in fix-android10-camera-getmemory-cookie.py fix-android10-fstab-sdcard.py fix-android10-gpu-bench.py fix-android10-camera-daemon-boot.py; do echo "== $s"; python3 $D/$s; done
# libkyf37_jpegcompat (camera JPEG shim) is built by the normal ROM build via PRODUCT_PACKAGES; test tools: build-locked.sh <log> kyf37_cam_snap_test kyf37_dlopen_test
