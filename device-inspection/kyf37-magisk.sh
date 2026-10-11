#!/system/bin/sh
# KYF37: start the Magisk daemon (root for apps via the Magisk app). Runs from init service kyf37-magisk after boot.
# Magisk v23, runtime mode (no boot-image patch): SELinux is permissive on this ROM, so no policy injection is required.
LOG=/data/local/tmp/kyf37-magisk.log
exec >>$LOG 2>&1
echo "kyf37-magisk: $(date)"
[ "$(getprop persist.kyf37.magisk)" = 0 ] && { echo "disabled by persist.kyf37.magisk=0"; exit 0; }
M=/system/xbin/magisk
[ -x $M ] || { echo "missing $M"; exit 1; }
if ! $M -c >/dev/null 2>&1; then echo "magisk binary not runnable"; exit 1; fi
chmod 711 /data/local/tmp 2>/dev/null
mkdir -p /data/adb; chmod 700 /data/adb
# Lineage userdebug ships its own /system/xbin/su; shadow it with magisk (applet name = argv[0])
mount | grep -q ' /system/xbin/su ' || mount -o bind $M /system/xbin/su
$M --daemon
i=0; while [ $i -lt 20 ] && ! $M -V >/dev/null 2>&1; do sleep 1; i=$((i+1)); done
echo "magisk $($M -v) ($($M -V))"
# adb shell (uid 2000) may use su without a prompt, matching the earlier root setup; apps are managed by the Magisk app
$M --sqlite 'REPLACE INTO policies (uid,policy,until,logging,notification) VALUES (2000,2,0,1,1)'
/system/xbin/su -c id
