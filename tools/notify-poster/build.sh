#!/bin/bash
# Builds Post.jar (dex) using the AOSP tree javac + d8. Run in WSL.
R=/home/pablo/kyf37-android10; W=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/tools/notify-poster; T=/tmp/notify-poster
rm -rf $T; mkdir -p $T/cls
FW=$R/out/soong/.intermediates/frameworks/base/framework/android_common/turbine-combined/framework.jar
[ -f $FW ] || FW=$(ls $R/out/soong/.intermediates/frameworks/base/framework/android_common/*/framework.jar | head -1)
$R/prebuilts/jdk/jdk9/linux-x86/bin/javac -source 8 -target 8 -cp $FW -d $T/cls $W/Post.java 2>&1 | grep -v "^Note\|warning"
$R/prebuilts/jdk/jdk9/linux-x86/bin/jar cf $T/post.jar -C $T/cls .
export LD_LIBRARY_PATH=$R/out/host/linux-x86/lib64; export PATH=$R/prebuilts/jdk/jdk9/linux-x86/bin:$PATH
$R/out/soong/host/linux-x86/bin/d8 --min-api 29 --output $T $T/post.jar 2>&1 | head -5
cd $T && zip -q $W/Post.jar classes.dex && ls -l $W/Post.jar
