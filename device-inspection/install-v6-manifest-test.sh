#!/sbin/sh
set -eu
B=/sbin/busybox
hash() { $B sha256sum "$1" | $B awk '{print $1}'; }
[ "$(getprop ro.serialno)" = 981108631314 ]
[ "$(cat /sys/class/block/mmcblk0p15/start)" = 290816 ]
[ "$(hash /system/vendor/etc/vintf/manifest.xml)" = 7109e1095d4463272cfd5b0f47934f4cd19337d33c274a3e8a07d8a51a3abc3e ]
[ "$(hash /tmp/v6-device-manifest.xml)" = f049b60ac2f85bf0ac4106dcd5b12f582683bf7c2fc3fca61b42132e223f2acc ]
[ "$(hash /tmp/clear-system-temp-wp)" = 958575ecb6b1a4a8f6d909f22a7412adfef03861bad1782b2b3baccd7bb5b9c9 ]
[ ! -e /cache/kyf37-manifest-before-v6.xml ]
$B cp /system/vendor/etc/vintf/manifest.xml /cache/kyf37-manifest-before-v6.xml
[ "$(hash /cache/kyf37-manifest-before-v6.xml)" = 7109e1095d4463272cfd5b0f47934f4cd19337d33c274a3e8a07d8a51a3abc3e ]
$B chmod 755 /tmp/clear-system-temp-wp
/tmp/clear-system-temp-wp --clear-system-temporary
$B cp /tmp/v6-device-manifest.xml /system/vendor/etc/vintf/manifest.xml
$B chmod 644 /system/vendor/etc/vintf/manifest.xml
$B chown 0:0 /system/vendor/etc/vintf/manifest.xml
chcon u:object_r:vendor_configs_file:s0 /system/vendor/etc/vintf/manifest.xml
$B sync
[ "$(hash /system/vendor/etc/vintf/manifest.xml)" = f049b60ac2f85bf0ac4106dcd5b12f582683bf7c2fc3fca61b42132e223f2acc ]
echo VINTF_MANIFEST_CORRECTION_VERIFIED
