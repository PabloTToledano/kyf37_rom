#!/sbin/sh
set -eu
B=/sbin/busybox
[ "$(getprop ro.serialno)" = 981108631314 ]
[ "$(getprop ro.product.model)" = KYF37 ]
[ "$(cat /sys/class/block/mmcblk0p10/start)" = 151552 ]
[ "$($B blockdev --getsize64 /dev/block/mmcblk0p10)" = 16777216 ]
hash() { $B sha256sum "$1" | $B awk '{print $1}'; }
[ "$(hash /dev/block/mmcblk0p10)" = 99d834db59b5f384ae5d7600d5989743e05c343f63f9d8d61cdb245036f6bda9 ]
[ "$(hash /tmp/boot-kernel-test-signed.img)" = 6146f54eea8af89a7c8979a57a75084656d04591d51e33135e4efacb86fa13f8 ]
[ "$(hash /dev/block/mmcblk0p11)" = 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e ]
[ "$(hash /dev/block/mmcblk0p25)" = 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c ]
[ "$(hash /tmp/clear-recovery-boot-temp-wp)" = faf20446c1196ae8289344eb1585450c9f18e3a34e3491bd5f150751843ab550 ]
$B chmod 0755 /tmp/clear-recovery-boot-temp-wp
/tmp/clear-recovery-boot-temp-wp --clear-boot-recovery-temporary
$B dd if=/tmp/boot-kernel-test-signed.img of=/dev/block/mmcblk0p10 bs=4096
$B sync
[ "$(hash /dev/block/mmcblk0p10)" = 6146f54eea8af89a7c8979a57a75084656d04591d51e33135e4efacb86fa13f8 ]
[ "$(hash /dev/block/mmcblk0p11)" = 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e ]
[ "$(hash /dev/block/mmcblk0p25)" = 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c ]
echo DIAGNOSTIC_BOOT_WRITE_VERIFIED
