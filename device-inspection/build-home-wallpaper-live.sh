#!/bin/bash
# Repackage the compiled launcher with its updated manifest, then platform-sign.
# Run only after Kyf37Home's target Package step succeeds in build-locked.sh.
set -euo pipefail
R=/home/pablo/kyf37-android10
W=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection
T=$(mktemp -d /tmp/kyf37-home-wallpaper.XXXXXX)
trap 'rm -rf "$T"' EXIT
unzip -p "$R/out/target/product/kyf37/obj/APPS/Kyf37Home_intermediates/package.apk" classes.dex > "$T/classes.dex"
"$R/prebuilts/sdk/tools/linux/bin/aapt2" link -I "$R/prebuilts/sdk/29/public/android.jar" --manifest "$R/packages/apps/Kyf37Home/AndroidManifest.xml" -A "$R/packages/apps/Kyf37Home/assets" -o "$T/home.apk"
(cd "$T" && zip -q home.apk classes.dex)
bash "$W/sign-test-apk.sh" "$T/home.apk" "$W/wallpaper/Kyf37Home-wallpaper.apk"
