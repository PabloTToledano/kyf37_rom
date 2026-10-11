#!/system/bin/sh
# Preserve this ROM's xbin tools when exposing the existing Magisk runtime.
set -e
ROOTBIN=/data/local/tmp/kyf37-rom-root-xbin
chmod 711 /data/local/tmp
mkdir -p "$ROOTBIN"
chmod 755 "$ROOTBIN"
OVERLAID=0
while read source target rest; do
    if [ "$target" = /system/xbin ]; then OVERLAID=1; fi
done < /proc/mounts
if [ "$OVERLAID" = 0 ]; then
    cp -R /system/xbin/. "$ROOTBIN/"
else
    # A different mount must not be silently replaced or stacked.
    [ -L /system/xbin/magisk ]
    [ "$(readlink /system/xbin/magisk)" = /data/local/tmp/magisk ]
    [ -L /system/xbin/su ]
    [ "$(readlink /system/xbin/su)" = magisk ]
    [ /system/xbin -ef "$ROOTBIN" ]
fi
ln -sf /data/local/tmp/magisk "$ROOTBIN/magisk"
ln -sf magisk "$ROOTBIN/su"
if [ "$OVERLAID" = 0 ]; then mount -o bind "$ROOTBIN" /system/xbin; fi
/system/xbin/su -c id
