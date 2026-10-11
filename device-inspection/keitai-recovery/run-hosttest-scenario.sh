#!/bin/bash
# usage: run-hosttest-scenario.sh <scenario.json> <outdir-name>   (restarts TWRP, runs the scenario, copies frames)
set -e
H=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
bash $H/device-inspection/run-hosttest.sh >/dev/null
# wait until TWRP drew its first real page
for i in $(seq 1 120); do grep -q "Set page: 'system_readonly'\|Set page: 'main2'" /home/pablo/kyf37-twrp-hosttest/root/tmp/recovery.log 2>/dev/null && break; sleep 1; done
sleep 3
OUT=$H/kyf37-twrp-device/keitai/hosttest/$2
rm -rf $OUT; mkdir -p $OUT
python3 $H/device-inspection/keitai-recovery/hosttest-drive.py $H/device-inspection/keitai-recovery/scenarios/$1 $OUT
