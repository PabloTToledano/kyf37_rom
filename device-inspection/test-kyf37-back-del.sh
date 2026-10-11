#!/bin/bash
# Host-side unit test of the Clear/Back -> backspace rule (WSL). Needs only the AOSP JDK.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
JDK=/home/pablo/kyf37-android10/prebuilts/jdk/jdk9/linux-x86/bin
W=$(mktemp -d)
mkdir -p $W/android/view
cp $HERE/Kyf37BackDelPolicy.java.txt $W/android/view/Kyf37BackDelPolicy.java
cp $HERE/Kyf37BackDelPolicyTest.java.txt $W/android/view/Kyf37BackDelPolicyTest.java
$JDK/javac -d $W/out $W/android/view/*.java
$JDK/java -cp $W/out android.view.Kyf37BackDelPolicyTest
rm -rf $W
