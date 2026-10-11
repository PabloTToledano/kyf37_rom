#!/system/bin/sh
set -e
chmod 711 /data/local/tmp
ROOTBIN=/data/local/tmp/kyf37-root-xbin
mkdir -p "$ROOTBIN"
chmod 755 "$ROOTBIN"
OVERLAID=0
while read source target rest; do
    if [ "$target" = /system/xbin ]; then OVERLAID=1; fi
done < /proc/mounts
if [ "$OVERLAID" = 0 ]; then
    cp /system/xbin/dexdump "$ROOTBIN/dexdump"
    cp /system/xbin/sqlite3 "$ROOTBIN/sqlite3"
else
    # Do not copy a bind-mounted file onto itself or stack another mount.
    [ -f "$ROOTBIN/dexdump" ] && [ -f "$ROOTBIN/sqlite3" ]
    [ -L /system/xbin/su ]
    [ "$(readlink /system/xbin/su)" = magisk ]
fi
ln -sf /data/local/tmp/magisk "$ROOTBIN/magisk"
chmod 755 "$ROOTBIN/dexdump" "$ROOTBIN/sqlite3"
ln -sf magisk "$ROOTBIN/su"
if [ "$OVERLAID" = 0 ]; then mount -o bind "$ROOTBIN" /system/xbin; fi
ls -l /system/xbin/su
