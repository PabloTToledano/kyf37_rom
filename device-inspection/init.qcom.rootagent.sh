#!/system/bin/sh
# KYF37: start the existing runtime Magisk setup through the stock rootagent hook.
# Removal: set persist.sys.rootagent=0 and remove this script from /system/etc.
attempt=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$attempt" -lt 120 ]; do
    sleep 1
    attempt=$((attempt + 1))
done
exec >>/data/local/tmp/kyf37-root-startup.log 2>&1
echo "KYF37 root startup: $(date)"
if [ ! -x /data/local/tmp/magisk ] || [ ! -f /data/local/tmp/enable-app-root.sh ]; then
    echo 'Required runtime root files missing'
    exit 1
fi
/data/local/tmp/magisk --daemon
chmod 711 /data/local/tmp
/data/local/tmp/magisk --sqlite 'REPLACE INTO policies (uid,policy,until,logging,notification) VALUES (2000,2,0,1,1)'
if [ -f /system/etc/enable-rom-app-root.sh ]; then
    sh /system/etc/enable-rom-app-root.sh
else
    sh /data/local/tmp/enable-app-root.sh
fi
echo "Root setup exit=$?"
/system/xbin/su -c id
