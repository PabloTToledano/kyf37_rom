#!/bin/bash
# Quick syntax/type check of a keitai app against the Android 10 SYSTEM SDK jar (no AOSP build). usage: javac-check.sh dialer|contacts|messages
set -e
APP=$1
R=/home/pablo/kyf37-android10
W=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection
OUT=/tmp/kc-$APP
rm -rf $OUT; mkdir -p $OUT/src/org/kyf37/$APP $OUT/cls
cp $W/keitai-apps/$APP/*.java $OUT/src/org/kyf37/$APP/
for f in $W/keitai-apps/common/*.java; do sed "s/@PKG@/org.kyf37.$APP/g" $f > $OUT/src/org/kyf37/$APP/$(basename $f); done
if [ "$APP" != contacts ]; then sed "s/@PKG@/org.kyf37.$APP/g" $W/keitai-apps/role/RoleBoot.java > $OUT/src/org/kyf37/$APP/RoleBoot.java; fi
sed "s/@PKG@/org.kyf37.$APP/g" $W/Kyf37FocusCompat.java.txt > $OUT/src/org/kyf37/$APP/Kyf37FocusCompat.java
$R/prebuilts/jdk/jdk9/linux-x86/bin/javac -Xlint:-options -encoding UTF-8 -cp $R/prebuilts/sdk/29/system/android.jar -d $OUT/cls $OUT/src/org/kyf37/$APP/*.java 2>&1 | head -${2:-60}
echo "javac done for $APP"
