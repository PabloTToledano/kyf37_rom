#!/bin/bash
set -euo pipefail
tree=/home/pablo/kyf37-lineage
task_root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
compiler=$tree/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gcc
"$compiler" -std=c99 -Wall -Wextra -Werror -fPIC -march=armv7-a -mfloat-abi=softfp \
 -I"$tree/bionic/libc/arch-arm/include" -I"$tree/bionic/libc/include" \
 -I"$tree/bionic/libc/kernel/uapi" -I"$tree/bionic/libc/kernel/uapi/asm-arm" \
 -c "$task_root/kyf37-rom/navigation/subdisplay/framebuffer.c" \
 -o /home/pablo/kyf37-rom/subdisplay-framebuffer-arm.o
file /home/pablo/kyf37-rom/subdisplay-framebuffer-arm.o
