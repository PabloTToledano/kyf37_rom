#!/bin/bash
nohup setsid bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-locked.sh "$1" SystemUI >/dev/null 2>&1 </dev/null &
