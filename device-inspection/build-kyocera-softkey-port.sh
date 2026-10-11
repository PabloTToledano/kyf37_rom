#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
stage=/home/pablo/kyf37-rom/kyocera-compat
jdk=/home/pablo/kyf37-host-tools/jdk8/bin
mkdir -p "$stage/classes" "$stage/app-smali"
"$jdk/javac" -source 7 -target 7 -bootclasspath "$workspace/kyf37-rom/android-7-sdk-classes.jar" -d "$stage/classes" "$workspace/kyf37-rom/kyocera-compat/src/jp/kyocera/kcfp/util/"*.java
"$jdk/java" -jar /home/pablo/kyf37-lineage/prebuilts/sdk/tools/lib/dx.jar --dex --output="$stage/softkey-compat.dex" "$stage/classes"
"$jdk/java" -jar /home/pablo/kyf37-rom/tools/baksmali.jar disassemble "$stage/softkey-compat.dex" -o "$stage/helper-smali"
cp -a /home/pablo/kyf37-rom/afphome-port-smali/. "$stage/app-smali/"
cp -a "$stage/helper-smali/." "$stage/app-smali/"
python3 "$workspace/device-inspection/port-afphome-overflow.py" "$stage/app-smali"
"$jdk/java" -jar /home/pablo/kyf37-rom/tools/smali.jar assemble "$stage/app-smali" -o "$workspace/kyf37-rom/AfpHome-softkey-port.dex"
cp "$stage/softkey-compat.dex" "$workspace/kyf37-rom/kyocera-compat/softkey-compat.dex"
sha256sum "$workspace/kyf37-rom/AfpHome-softkey-port.dex" "$workspace/kyf37-rom/kyocera-compat/softkey-compat.dex"
