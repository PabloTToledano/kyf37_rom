#!/sbin/sh
set -eu
B=/sbin/busybox
[ "$(getprop ro.serialno)" = 981108631314 ]
[ "$(getprop ro.product.model)" = KYF37 ]
[ "$(cat /sys/class/block/mmcblk0p10/start)" = 151552 ]
[ "$($B blockdev --getsize64 /dev/block/mmcblk0p10)" = 16777216 ]
hash() { $B sha256sum "$1" | $B awk '{print $1}'; }
[ "$(hash /dev/block/mmcblk0p10)" = cd5e3b00e83b404a321b19650c7d0c458577b6a141d657a4097139b873c36f2f ]
[ "$(hash /tmp/boot-kernel-test-signed.img)" = bbc4a842f789a8b80ca9141bbd8bdd7069663d915191c90a62935e94502cbfce ]
[ "$(hash /dev/block/mmcblk0p11)" = 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e ]
[ "$(hash /dev/block/mmcblk0p25)" = 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c ]
[ "$(hash /tmp/clear-recovery-boot-temp-wp)" = faf20446c1196ae8289344eb1585450c9f18e3a34e3491bd5f150751843ab550 ]
$B mountpoint -q /external_sd
[ ! -e /external_sd/NOTPUSH ] && [ ! -e /external_sd/CHKCODE ] && [ ! -e /external_sd/FASTBOOT ] && [ ! -e /external_sd/SDDLFLAG ]
[ ! -e /external_sd/kyf37-v3-boot-before-kernel-test.img ]
$B dd if=/dev/block/mmcblk0p10 of=/external_sd/kyf37-v3-boot-before-kernel-test.img bs=1048576
[ "$(hash /external_sd/kyf37-v3-boot-before-kernel-test.img)" = cd5e3b00e83b404a321b19650c7d0c458577b6a141d657a4097139b873c36f2f ]
$B chmod 0755 /tmp/clear-recovery-boot-temp-wp
/tmp/clear-recovery-boot-temp-wp --clear-boot-recovery-temporary
$B dd if=/tmp/boot-kernel-test-signed.img of=/dev/block/mmcblk0p10 bs=4096
$B sync
[ "$(hash /dev/block/mmcblk0p10)" = bbc4a842f789a8b80ca9141bbd8bdd7069663d915191c90a62935e94502cbfce ]
[ "$(hash /dev/block/mmcblk0p11)" = 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e ]
[ "$(hash /dev/block/mmcblk0p25)" = 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c ]
echo DIAGNOSTIC_BOOT_WRITE_VERIFIED
