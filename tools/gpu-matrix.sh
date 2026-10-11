#!/bin/bash
# usage: gpu-matrix.sh  (phone lock required). Cores=4, CPU min 533 MHz; varies GPU min_freq and idle_timer.
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
set_cfg(){ timeout 40 $A shell "echo 4 > /sys/devices/system/cpu/cpu0/core_ctl/min_cpus; sleep 1; for c in 0 1 2 3; do echo 533333 > /sys/devices/system/cpu/cpu\$c/cpufreq/scaling_min_freq 2>/dev/null; done; echo $1 > /sys/class/kgsl/kgsl-3d0/devfreq/min_freq; echo $2 > /sys/class/kgsl/kgsl-3d0/idle_timer" >/dev/null 2>&1; }
run(){ bash tools/gpu-jank-test.sh "$1" 2>&1 | grep -E "Janky|95th" | tr '\n' ' '; echo; }
for rep in 1 2; do
 set_cfg 307200000 200;  run "min307-idle200-$rep"
 set_cfg 409600000 50;   run "min409-idle50-$rep"
 set_cfg 200000000 1000; run "min200-idle1000-$rep"
 set_cfg 307200000 1000; run "min307-idle1000-$rep"
done
echo DONE
