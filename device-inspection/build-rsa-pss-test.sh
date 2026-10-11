#!/bin/bash
set -euo pipefail
tree=/home/pablo/kyf37-lineage
task_root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
compiler=$tree/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gcc
libs=$tree/out/target/product/kyf37/obj/lib
startup=$tree/prebuilts/ndk/current/platforms/android-21/arch-arm/usr/lib
test_flags=()
test_output=rsa-pss-compat-test
if [[ ${1:-} == --exported ]]; then
 test_flags=(-DKYF37_TEST_EXPORTED)
 test_output=rsa-pss-export-test
fi
"$compiler" -nostdlib -fPIE -pie -march=armv7-a -mfloat-abi=softfp \
 -I"$tree/external/boringssl/src/include" \
 -I"$tree/bionic/libc/arch-arm/include" -I"$tree/bionic/libc/include" \
 -I"$tree/bionic/libc/kernel/uapi" -I"$tree/bionic/libc/kernel/uapi/asm-arm" \
 "${test_flags[@]}" "$startup/crtbegin_dynamic.o" "$task_root/device-inspection/rsa-pss-compat-test.c" \
 -L"$libs" -lcrypto -lc -lm -lstdc++ "$startup/crtend_android.o" \
 -Wl,--dynamic-linker,/system/bin/linker -o "$task_root/device-inspection/$test_output"
cp "$tree/out/target/product/kyf37/obj/SHARED_LIBRARIES/libcrypto_intermediates/LINKED/libcrypto.so" \
 "$task_root/device-inspection/rsa-test-libcrypto.so"
