#!/bin/bash
# usage: stage-systemui.sh <iteration-name>  -> signed APK in kyf37-rom/systemui-loop/apk/SystemUI-<name>.apk
O=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/systemui-loop/apk
mkdir -p $O
bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/sign-test-apk.sh /home/pablo/kyf37-android10/out/target/product/kyf37/system/product/priv-app/SystemUI/SystemUI.apk $O/SystemUI-$1.apk
sha256sum $O/SystemUI-$1.apk
