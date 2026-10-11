#!/bin/bash
# Serialise ROM builds: only one soong/ninja build may run in ~/kyf37-android10. Usage: build-locked.sh [logfile]
LOG=${1:-$HOME/kyf37-android10-build-$(date +%H%M%S).log}
if [ "$#" -gt 0 ]; then shift; fi
exec 9>$HOME/kyf37-build.lock
echo "waiting for build lock ($(date +%T))" >> "$LOG"
flock 9
echo "build lock acquired ($(date +%T))" >> "$LOG"
if [ "${1:-}" = "--staged-ui" ]; then
    bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-staged-keypad-ui.sh >> "$LOG" 2>&1
elif [ "${1:-}" = "--staged-dialer" ]; then
    bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-staged-dialer.sh >> "$LOG" 2>&1
elif [ "${1:-}" = "--kernel" ]; then
    bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/apply-kyf37-kernel-fixes.sh >> "$LOG" 2>&1
else
    bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-kyf37-android10.sh "$@" >> "$LOG" 2>&1
fi
echo "BUILD_EXIT=$?" >> "$LOG"
