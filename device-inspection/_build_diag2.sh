#!/bin/bash
# Build kyf37_diag2 as a dynamic Android binary (bionic linker from the phone) with the Android 10 tree's clang.
T=$HOME/kyf37-android10
D=$T/prebuilts/clang/host/linux-x86/clang-r339409b/bin
GL=$T/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/lib/gcc/arm-linux-androideabi/4.9.x
CR=$T/out/soong/.intermediates/bionic/libc/crtbegin_dynamic/android_arm_armv7-a-neon_cortex-a7_core/crtbegin_dynamic.o
LIBC=$T/out/target/product/kyf37/system/apex/com.android.runtime.debug/lib/bionic/libc.so
SRC=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/kyf37_diag2.c
CL=$D/clang-8
mkdir -p /tmp/rcstub/linux && : > /tmp/rcstub/linux/compiler_types.h && cp /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/_stub_linux_compiler.h /tmp/rcstub/linux/compiler.h
"$CL" --target=arm-linux-androideabi -march=armv7-a -mfloat-abi=softfp -fPIE -nostdinc -isystem /tmp/rcstub \
  -isystem "$T/bionic/libc/include" -isystem "$T/bionic/libc/kernel/uapi" -isystem "$T/bionic/libc/kernel/uapi/asm-arm" \
  -isystem "$GL/include" -O2 -c "$SRC" -o /tmp/rc2.o && echo compiled
"$CL" --target=arm-linux-androideabi -pie -nostdlib -fuse-ld="$D/ld.lld" -Wl,--dynamic-linker=/system/bin/linker \
  -o "$HOME/kyf37_diag2" "$CR" /tmp/rc2.o "$LIBC" "$GL/libgcc.a" 2>&1 | grep -v warning | head -6
ls -l "$HOME/kyf37_diag2" 2>&1 | cut -c1-100
