#!/bin/bash
set -eo pipefail
cd /home/pablo/kyf37-android10
export PATH=/home/pablo/kyf37-host-tools/python2/bin:$PATH
export LD_LIBRARY_PATH=/home/pablo/kyf37-host-tools/legacy-libs/lib/x86_64-linux-gnu:/home/pablo/kyf37-host-tools/legacy-libs/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export LC_ALL=C
export BUILD_USERNAME=althia
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-build-branding.py
export MKE2FS_CONFIG=/home/pablo/kyf37-android10/system/extras/ext4_utils/mke2fs.conf
mkdir -p /home/pablo/kyf37-rom/kernel-android10-headers
command make -C /home/pablo/kyf37-rom/kernel-android10 O=/home/pablo/kyf37-rom/kernel-android10-headers ARCH=arm HOSTCC="gcc -std=gnu99 -fcommon" INSTALL_HDR_PATH=/home/pablo/kyf37-android10/out/target/product/kyf37/obj/KERNEL_OBJ/usr headers_install
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/filter-android10-kernel-headers.py /home/pablo/kyf37-android10/out/target/product/kyf37/obj/KERNEL_OBJ/usr/include
source build/envsetup.sh
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-home-legacy-restore.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-brightness.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-sensors.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-auto-brightness.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-settings-dpad.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-product-continuations.py
lunch lineage_kyf37-userdebug
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-native-guide-polish.py
if [ "$#" -eq 0 ]; then set -- bootimage systemimage; fi
case " $* " in
  *" systemimage "*|*" Kyf37OuterScreen "*|*" libkyf37subdisplay "*|*" libtinyalsa "*)
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-outer-animation.py
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-audio-pcm-config-abi.py
    ;;
esac
case " $* " in
  *" systemimage "*|*" KyoceraCamera "*|*" MemoPad "*|*" MemoPadProvider "*|*" Reader "*|*" kc_soundrecorder "*|*" kc_soundrecorder_manager "*)
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-native-softkeys.py
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-stock-storage-api.py
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-selected-stock-runtime.py
    ;;
esac
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-native-softkey-policy.py
# Apply the owner's final UI policy after any older staging scripts.
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-native-only-bars.py
# Keypad navigation / focus theme (KEYPAD-NAV.md). Order matters; all idempotent.
for kyf37_nav in focus-theme pointer-cursor keypad-nav-ui home-cursor focus-polish settings-homepage-focus setupwizard-keypad default-permissions adb-default systemui-shade systemui-material keitai-apps accent-blue default-ime ril-cardstatus ril-setupdata; do
  if [ -f /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-$kyf37_nav.py ]; then
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-$kyf37_nav.py
  fi
done
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-modern-lockscreen.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-home-folders.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-kyocera-classic.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-original-icon-fallback.py
case " $* " in
  *" systemimage "*|*" framework-res "*)
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-remaining-stock-resources.py
    ;;
esac
# Release hygiene (idempotent): boot-breaking leftovers are removed from the SOURCE and from the build OUTPUT, because
# Android's build never deletes installed files when a copy rule goes away (v17/v18 shipped stale TV files this way).
for kyf37_rel in remove-kyocera-public-libs remove-tv-apps microg-spoof-resref microg-official-signature radio-xmldecl magisk; do
  if [ -f /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-$kyf37_rel.py ]; then
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-$kyf37_rel.py
  fi
done
kyf37_out="$HOME/kyf37-android10/out/target/product/kyf37"
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-release-refinements.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-gallery.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-home-management.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-home-redesign.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-outer-v2.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-gpu-ui-perf.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-tama.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-keypad-system-polish.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-dialer-lid-close.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-kawaii-setup-keyguard.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/verify-kawaii-setup-keyguard.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/verify-keypad-system-polish.py
rm -f "$kyf37_out/system/etc/public.libraries-kyocera.txt"
rm -rf "$kyf37_out/system/app/FsDtvApp" "$kyf37_out/system/app/Kyf37Tv" "$kyf37_out/system/priv-app/FsDtvApp" "$kyf37_out/system/priv-app/Kyf37Tv"
# Build and merge the resource-free gallery DEX into the original Kyocera APK.
# Package-only target avoids shipping the code payload as a second installed app.
m -j8 out/target/product/kyf37/obj/APPS/Kyf37GalleryCode_intermediates/package.apk
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/merge-kyf37-gallery.py
python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/verify-gallery-port.py
mkdir -p /home/pablo/kyf37-rom/gallery-host-tests
prebuilts/jdk/jdk9/linux-x86/bin/javac -encoding UTF-8 -d /home/pablo/kyf37-rom/gallery-host-tests /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/kyf37-gallery/GalleryLogic.java /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/kyf37-gallery/GalleryLogicTest.java
prebuilts/jdk/jdk9/linux-x86/bin/java -cp /home/pablo/kyf37-rom/gallery-host-tests org.kyf37.gallery.GalleryLogicTest
m -j8 "$@"
