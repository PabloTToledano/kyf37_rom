#!/bin/bash
# cores x GPU-floor sweep for the screen-on profile (phone lock required)
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
set_cfg(){ timeout 40 $A shell "echo $1 > /sys/devices/system/cpu/cpu0/core_ctl/min_cpus; sleep 1; echo $2 > /sys/class/kgsl/kgsl-3d0/devfreq/min_freq" >/dev/null 2>&1; }
run(){ bash tools/gpu-jank-test.sh "$1" 2>&1 | grep -E "Janky|95th" | tr '\n' ' '; echo; }
for rep in 1 2; do
 set_cfg 3 307200000; run "cores3-gpu307-anim05-$rep"
 set_cfg 4 307200000; run "cores4-gpu307-anim05-$rep"
 set_cfg 2 307200000; run "cores2-gpu307-anim05-$rep"
 set_cfg 2 200000000; run "cores2-gpu200-anim05-$rep"
done
echo DONE
