#!/bin/bash
set -euo pipefail
task_root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
compiler=/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gcc
"$compiler" -nostdlib -static -Wl,-e,_start \
 "$task_root/device-inspection/kernel-interface-probe.S" \
 -o "$task_root/device-inspection/kernel-interface-probe"
file "$task_root/device-inspection/kernel-interface-probe"
