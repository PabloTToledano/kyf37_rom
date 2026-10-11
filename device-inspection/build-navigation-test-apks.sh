#!/bin/bash
set -eo pipefail
host=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
build=/home/pablo/kyf37-rom/navigation-apks
sdk=/home/pablo/kyf37-twrp/prebuilts/sdk
java=/home/pablo/kyf37-host-tools/jdk8/bin
mkdir -p "$build"
for module in ime home; do
    target="$build/$module"
    mkdir -p "$target/classes"
    "$java/javac" -source 1.7 -target 1.7 -encoding UTF-8 -cp "$sdk/current/android.jar" -d "$target/classes" $(find "$host/kyf37-rom/navigation/$module/src" -name '*.java')
    "$java/java" -jar "$sdk/tools/lib/dx.jar" --dex --output="$target/classes.dex" "$target/classes"
    args=()
    if [ -d "$host/kyf37-rom/navigation/$module/res" ]; then args=(-S "$host/kyf37-rom/navigation/$module/res"); fi
    "$sdk/tools/linux/aapt" package -f -M "$host/kyf37-rom/navigation/$module/AndroidManifest.xml" "${args[@]}" -I "$sdk/current/android.jar" -F "$target/unsigned.apk"
    (cd "$target"; "$sdk/tools/linux/aapt" add unsigned.apk classes.dex)
    "$java/java" -jar "$sdk/tools/lib/signapk.jar" /home/pablo/kyf37-twrp/build/target/product/security/testkey.x509.pem /home/pablo/kyf37-twrp/build/target/product/security/testkey.pk8 "$target/unsigned.apk" "$target/$module-test.apk"
    cp "$target/$module-test.apk" "$host/kyf37-rom/navigation/$module-test.apk"
done
