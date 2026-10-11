#!/bin/bash
# Build Kyf37OuterScreen, sign with the platform key, replace the system priv-app on the phone (WP cleared), reboot, wait. Run from repo root in Git Bash.
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe; R=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms
wsl -d Ubuntu -- bash -c "rm -f ~/outer2.log; cd ~ && bash $R/device-inspection/build-locked.sh /home/pablo/outer2.log Kyf37OuterScreen >/dev/null 2>&1; grep BUILD_EXIT ~/outer2.log"
wsl -d Ubuntu -- bash $R/device-inspection/sign-test-apk.sh /home/pablo/kyf37-android10/out/target/product/kyf37/system/priv-app/Kyf37OuterScreen/Kyf37OuterScreen.apk $R/kyf37-rom/Kyf37OuterScreen-v2.apk
wsl -d Ubuntu -- bash -c "cp ~/kyf37-android10/out/target/product/kyf37/system/lib/libkyf37subdisplay.so $R/kyf37-rom/libkyf37subdisplay.so"
$A root >/dev/null; sleep 3
$A push kyf37-rom/Kyf37OuterScreen-v2.apk /data/local/tmp/outer.apk >/dev/null; $A push kyf37-rom/libkyf37subdisplay.so /data/local/tmp/ >/dev/null
$A shell "/data/local/tmp/clear-system-temp-wp --clear-system-temporary | tail -1; mount -o remount,rw /system; D=/system/priv-app/Kyf37OuterScreen; cp /data/local/tmp/outer.apk \$D/Kyf37OuterScreen.apk; cp /data/local/tmp/libkyf37subdisplay.so \$D/lib/arm/; cp /data/local/tmp/libkyf37subdisplay.so /system/lib/; rm -rf \$D/oat; chmod 644 \$D/Kyf37OuterScreen.apk \$D/lib/arm/libkyf37subdisplay.so /system/lib/libkyf37subdisplay.so; chcon u:object_r:system_file:s0 \$D/Kyf37OuterScreen.apk \$D/lib/arm/libkyf37subdisplay.so /system/lib/libkyf37subdisplay.so; sync; mount -o remount,ro /system"
$A reboot; sleep 80; for i in $(seq 1 40); do [ "$($A shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && break; sleep 6; done; sleep 25
$A shell "ps -A | grep subdisplay; logcat -d -s KYF37OuterScreen:V | tail -5; dumpsys notification | grep -A2 'Live notification listeners'"
