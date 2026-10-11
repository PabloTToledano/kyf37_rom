#!/bin/bash
# Screen-off idle survey (60 s): interrupt deltas, wakeup sources, busiest processes, held wakelocks. Needs phone lock + adb root.
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
$A shell 'svc power stayon false; input keyevent KEYCODE_SLEEP; sleep 5
cat /proc/interrupts > /data/local/tmp/irq1; cat /proc/stat | head -1 > /data/local/tmp/stat1
for p in $(ls /proc | grep -E "^[0-9]+$"); do [ -r /proc/$p/stat ] && echo "$p $(cat /proc/$p/stat | cut -d" " -f2,14,15) $(cat /proc/$p/cmdline 2>/dev/null | tr "\0" " " | cut -c1-60)"; done > /data/local/tmp/p1
cat /sys/kernel/debug/wakeup_sources > /data/local/tmp/ws1 2>/dev/null
sleep 60
cat /proc/interrupts > /data/local/tmp/irq2; cat /proc/stat | head -1 > /data/local/tmp/stat2
for p in $(ls /proc | grep -E "^[0-9]+$"); do [ -r /proc/$p/stat ] && echo "$p $(cat /proc/$p/stat | cut -d" " -f2,14,15) $(cat /proc/$p/cmdline 2>/dev/null | tr "\0" " " | cut -c1-60)"; done > /data/local/tmp/p2
cat /sys/kernel/debug/wakeup_sources > /data/local/tmp/ws2 2>/dev/null
dumpsys power | grep -i -E "mWakefulness=|Wake Locks|PARTIAL|SCREEN_" | head -8'
for f in irq1 irq2 p1 p2 ws1 ws2 stat1 stat2; do $A pull /data/local/tmp/$f kyf37-rom/idle-$f.txt >/dev/null 2>&1; done
python tools/idle-survey-report.py
