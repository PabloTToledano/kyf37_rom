#!/bin/bash
# Start the host-test TWRP (qemu-arm user emulation) in the background; log: ~/hosttest.log
T=/home/pablo/kyf37-twrp-hosttest/root
pkill -9 -x qemu-arm 2>/dev/null || true; pkill -f 'sleep 100000' 2>/dev/null || true
rm -f $T/fb.raw $T/dev/input/event0
mkdir -p $T/dev/input $T/tmp
mkfifo $T/dev/input/event0
chmod 666 $T/dev/input/event0
cd /
# keep a writer on the fake input FIFO so TWRP's open() does not block
setsid nohup bash -c "exec 9<>$T/dev/input/event0; sleep 100000" >/dev/null 2>&1 < /dev/null &
setsid nohup unshare -r -m -p -f bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/hosttest-inner.sh > ~/hosttest.log 2>&1 < /dev/null &
disown
echo started
