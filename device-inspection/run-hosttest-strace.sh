#!/bin/bash
# Same as run-hosttest.sh but with qemu -strace into <chroot>/tmp/qemu-strace.log (slow!)
T=/home/pablo/kyf37-twrp-hosttest/root
pkill -9 -x qemu-arm 2>/dev/null
rm -f $T/dev/input/event0 $T/fb.raw $T/tmp/qemu-strace.log
mkfifo $T/dev/input/event0; chmod 666 $T/dev/input/event0
cd /
# keep a writer on the fake input FIFO so TWRP's open() does not block
setsid nohup bash -c "exec 9<>$T/dev/input/event0; sleep 100000" >/dev/null 2>&1 < /dev/null &
export QEMU_EXTRA='-strace -D /tmp/qemu-strace.log'
setsid nohup unshare -r -m -p -f bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/hosttest-inner.sh > ~/hosttest.log 2>&1 < /dev/null &
disown
echo started-strace
