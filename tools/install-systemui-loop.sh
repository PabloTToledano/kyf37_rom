#!/bin/bash
# usage: tools/install-systemui-loop.sh <SystemUI.apk>   (hold the phone lock as 'systemui-loop' first)
# SystemUI is persistent: pm install is refused, so the APK replaces the system copy (WP helper, remount rw, atomic mv).
# Rollback: tools/install-systemui-loop.sh kyf37-rom/systemui-loop/apk/SystemUI-v19-original.apk
export MSYS_NO_PATHCONV=1
A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
APK=$1; D=/system/product/priv-app/SystemUI
[ -f "$APK" ] || { echo "no apk"; exit 2; }
$A root >/dev/null 2>&1; sleep 2
$A push device-inspection/clear-system-temp-wp /data/local/tmp/ >/dev/null && $A shell chmod 755 /data/local/tmp/clear-system-temp-wp
$A push "$APK" /data/local/tmp/SystemUI-loop.apk >/dev/null || exit 3
$A shell '/data/local/tmp/clear-system-temp-wp --clear-system-temporary > /data/local/tmp/loop-wp.log 2>&1'
$A shell 'mount -o remount,rw /system' || exit 4
$A shell "mkdir -p /data/local/tmp/systemui-loop-rollback; [ -f /data/local/tmp/systemui-loop-rollback/SystemUI.apk ] || { cp -p $D/SystemUI.apk /data/local/tmp/systemui-loop-rollback/; [ -d $D/oat ] && cp -rp $D/oat /data/local/tmp/systemui-loop-rollback/; }"
$A shell "cp /data/local/tmp/SystemUI-loop.apk $D/SystemUI.apk.new && chown 0:0 $D/SystemUI.apk.new && chmod 644 $D/SystemUI.apk.new && restorecon $D/SystemUI.apk.new && mv $D/SystemUI.apk.new $D/SystemUI.apk && { [ -d $D/oat ] && rm -rf $D/oat-stale && mv $D/oat $D/oat-stale; true; }; sync"
RC=$?
$A shell 'sync; mount -o remount,ro /system'
[ $RC -eq 0 ] || { echo "replace failed"; exit 5; }
$A shell 'kill $(pidof com.android.systemui)'
sleep 12
$A shell pidof com.android.systemui || { echo "SystemUI did not restart"; exit 6; }
$A shell "sha256sum $D/SystemUI.apk"
