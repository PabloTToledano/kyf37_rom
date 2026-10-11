#!/bin/bash
# Build the keitai recovery in the dedicated TWRP tree (~/kyf37-twrp). Log: ~/twrp-keitai-build.log
setsid nohup bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-kyf37-twrp.sh > ~/twrp-keitai-build.log 2>&1 < /dev/null &
disown
echo started
