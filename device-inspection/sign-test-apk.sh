#!/bin/bash
# usage: sign-test-apk.sh in.apk out.apk   (platform key, for live "adb install -r" testing of ported apps)
R=/home/pablo/kyf37-android10
export LD_LIBRARY_PATH=$R/out/host/linux-x86/lib64
$R/prebuilts/jdk/jdk9/linux-x86/bin/java -Djava.library.path=$R/out/host/linux-x86/lib64 -jar $R/out/host/linux-x86/framework/signapk.jar $R/build/make/target/product/security/platform.x509.pem $R/build/make/target/product/security/platform.pk8 "$1" "$2"
