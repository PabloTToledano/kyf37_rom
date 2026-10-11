#!/bin/bash
# usage: shade-iter.sh <name>  -> build SystemUI through the locked wrapper, sign, stage kyf37-rom/systemui-loop/apk/SystemUI-<name>.apk
L=/home/pablo/shade-$1.log; rm -f $L
bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-locked.sh $L SystemUI >/dev/null 2>&1
grep -n "error:\|Error\b" $L | head -10
tail -2 $L
grep -q "BUILD_EXIT=0" $L && bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/stage-systemui.sh $1
