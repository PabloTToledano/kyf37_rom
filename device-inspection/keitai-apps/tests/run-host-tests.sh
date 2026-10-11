#!/bin/bash
# Runs the pure-Java host tests (MMS PDU codec, vCard) against android.jar stubs. usage: run-host-tests.sh
set -e
R=/home/pablo/kyf37-android10
W=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/keitai-apps
JAVAC=$R/prebuilts/jdk/jdk9/linux-x86/bin/javac
JAVA=$R/prebuilts/jdk/jdk9/linux-x86/bin/java
AJ=$R/prebuilts/sdk/29/system/android.jar
for app in messages contacts; do
  bash $W/javac-check.sh $app >/dev/null
  T=/tmp/kc-$app
  mkdir -p $T/tcls
  if [ $app = messages ]; then TEST=MmsHostTest; else TEST=VCardHostTest; fi
  cp $W/tests/$TEST.java $T/$TEST.java
  $JAVAC -Xlint:-options -encoding UTF-8 -cp $AJ:$T/cls -d $T/tcls $T/$TEST.java
  echo "== $app host test"
  $JAVA -cp $AJ:$T/cls:$T/tcls org.kyf37.$app.$TEST
done
