#!/sbin/sh
set -eu
B=/sbin/busybox
[ "$(getprop ro.serialno)" = 981108631314 ]
[ ! -e /system/rfs ]
[ "$($B sha256sum /dev/block/mmcblk0p11 | $B awk '{print $1}')" = 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e ]
[ "$($B sha256sum /tmp/clear-system-temp-wp | $B awk '{print $1}')" = 958575ecb6b1a4a8f6d909f22a7412adfef03861bad1782b2b3baccd7bb5b9c9 ]
$B chmod 755 /tmp/clear-system-temp-wp
/tmp/clear-system-temp-wp --clear-system-temporary
$B tar -xf /tmp/stock-rfs-layout.tar -C /system
chcon -R u:object_r:system_file:s0 /system/rfs
[ "$($B readlink /system/rfs/msm/mpss/readonly/firmware)" = /firmware ]
[ "$($B readlink /system/rfs/msm/mpss/readwrite)" = /persist/rfs/msm/mpss ]
$B sync
echo STOCK_RFS_LAYOUT_RESTORED
