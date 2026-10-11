#!/bin/bash
# Usage: start-keynav-build.sh <logname> [make targets...]   (starts a locked background build)
LOG=/home/pablo/$1; shift
nohup setsid bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-locked.sh "$LOG" "$@" >/dev/null 2>&1 </dev/null &
sleep 3
tail -n 2 "$LOG"
