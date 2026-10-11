#!/sbin/sh
set -eu
B=/sbin/busybox
hash() { $B sha256sum "$1" | $B awk '{print $1}'; }
[ "$(getprop ro.serialno)" = 981108631314 ]
[ "$(hash /dev/block/mmcblk0p11)" = 9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e ]
[ "$(hash /dev/block/mmcblk0p25)" = 0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c ]
[ -d /cache/kyf37-display-before-v6 ]
[ "$(hash /system/lib/liboverlay.so)" = 6c054fc6aa7d833a7b8e48d46d30f4bc068b534c6edcc062d2feeecd0a701791 ]
[ "$(hash /tmp/v6-display-providers/lib/liboverlay.so)" = 3f5edf1d137ba9ee869a3a61cabf854af83889e90cb0a0e4d87527de54eba31d ]
[ "$(hash /system/lib/libhdmi.so)" = 875c7827120aaba3225129451585d47c5680fa0fe206aede0de7cf80ca6ed8ba ]
[ "$(hash /tmp/v6-display-providers/lib/libhdmi.so)" = 87c7cfea41965838dcabd0bf31572aabf9d30960ef049389bf0b8ffb24549f40 ]
[ "$(hash /system/lib/libqdutils.so)" = 9edefb2e0417b91e6e10c29cb19b23ea284d962dad370979000457685db2ffbd ]
[ "$(hash /tmp/v6-display-providers/lib/libqdutils.so)" = e69243e85a60f061bf038fd0a830904de0c13d2956a62d8d5e1d303833cdd6da ]
[ "$(hash /system/lib/libmemalloc.so)" = 46db99914b29f4de17b022458fe69eef3aee71cea8418c3f5d7f8af5233be050 ]
[ "$(hash /tmp/v6-display-providers/lib/libmemalloc.so)" = 3570380ac3c4baf22541a00420db94ad908bb2b482b19ad58192618efb1222e9 ]
[ "$(hash /system/lib/libqdMetaData.so)" = e70a53925d03f98bab5dc76fe0f614f77a6359e97243e2dd8029ec51f21f4b39 ]
[ "$(hash /tmp/v6-display-providers/lib/libqdMetaData.so)" = 70fc4d54581939670c117beb2a9918fdd75d3ec17fb0666bab56a3b55f37160c ]
[ "$(hash /system/lib/libqservice.so)" = 9f1b6a7a8d1866d6191cc79eb8c471b893bafc93e7572249063dacaa6fcff0c9 ]
[ "$(hash /tmp/v6-display-providers/lib/libqservice.so)" = 803aff49e258b654090de8a0b3714cce20d66e35c5fca54bb7eb10e1f1638fe2 ]
[ "$(hash /system/lib/hw/hwcomposer.msm8909.so)" = 499bbd536bbf2a96fe611ba300b8f7aeb0dbdaf33cada7dc19af6cf1b880acbd ]
[ "$(hash /tmp/v6-display-providers/lib/hw/hwcomposer.msm8909.so)" = d5013a7173d1b229ccf6658ee3a03cffc07a8794c0085d0f23073b9daa02f269 ]
[ "$(hash /system/lib/hw/gralloc.msm8909.so)" = c3297037e49580bc1ec8250fd023c949aa2ac43d340be941567a76d2fe505844 ]
[ "$(hash /tmp/v6-display-providers/lib/hw/gralloc.msm8909.so)" = 34cee9437c17f3c1e37dd2f68f0b2c9f234d7db6f1641f0538255d284d527bde ]
[ "$(hash /system/lib/hw/copybit.msm8909.so)" = 56a5df8b26d7bf3412533dbd526fb1120db42f997a27c93ac5eeb155e62d2aef ]
[ "$(hash /tmp/v6-display-providers/lib/hw/copybit.msm8909.so)" = cf40d5802defbad61241c49ab5a6c991f651ccc6eedf49192b9c23cf59e69454 ]
[ "$(hash /system/lib/hw/memtrack.msm8909.so)" = bbf47cc31d68817b0e3c07b4afb34e728dc15f5572ddf12769a2653e8e3546b4 ]
[ "$(hash /tmp/v6-display-providers/lib/hw/memtrack.msm8909.so)" = e2c240a9d368525764df6e433a59667be29ff16d5c09cddb24d54464ca626112 ]
mkdir -p /cache/kyf37-display-before-v6/lib/hw
$B cp /system/lib/liboverlay.so /cache/kyf37-display-before-v6/lib/liboverlay.so
[ "$(hash /cache/kyf37-display-before-v6/lib/liboverlay.so)" = 6c054fc6aa7d833a7b8e48d46d30f4bc068b534c6edcc062d2feeecd0a701791 ]
$B cp /system/lib/libhdmi.so /cache/kyf37-display-before-v6/lib/libhdmi.so
[ "$(hash /cache/kyf37-display-before-v6/lib/libhdmi.so)" = 875c7827120aaba3225129451585d47c5680fa0fe206aede0de7cf80ca6ed8ba ]
$B cp /system/lib/libqdutils.so /cache/kyf37-display-before-v6/lib/libqdutils.so
[ "$(hash /cache/kyf37-display-before-v6/lib/libqdutils.so)" = 9edefb2e0417b91e6e10c29cb19b23ea284d962dad370979000457685db2ffbd ]
$B cp /system/lib/libmemalloc.so /cache/kyf37-display-before-v6/lib/libmemalloc.so
[ "$(hash /cache/kyf37-display-before-v6/lib/libmemalloc.so)" = 46db99914b29f4de17b022458fe69eef3aee71cea8418c3f5d7f8af5233be050 ]
$B cp /system/lib/libqdMetaData.so /cache/kyf37-display-before-v6/lib/libqdMetaData.so
[ "$(hash /cache/kyf37-display-before-v6/lib/libqdMetaData.so)" = e70a53925d03f98bab5dc76fe0f614f77a6359e97243e2dd8029ec51f21f4b39 ]
$B cp /system/lib/libqservice.so /cache/kyf37-display-before-v6/lib/libqservice.so
[ "$(hash /cache/kyf37-display-before-v6/lib/libqservice.so)" = 9f1b6a7a8d1866d6191cc79eb8c471b893bafc93e7572249063dacaa6fcff0c9 ]
$B cp /system/lib/hw/hwcomposer.msm8909.so /cache/kyf37-display-before-v6/lib/hw/hwcomposer.msm8909.so
[ "$(hash /cache/kyf37-display-before-v6/lib/hw/hwcomposer.msm8909.so)" = 499bbd536bbf2a96fe611ba300b8f7aeb0dbdaf33cada7dc19af6cf1b880acbd ]
$B cp /system/lib/hw/gralloc.msm8909.so /cache/kyf37-display-before-v6/lib/hw/gralloc.msm8909.so
[ "$(hash /cache/kyf37-display-before-v6/lib/hw/gralloc.msm8909.so)" = c3297037e49580bc1ec8250fd023c949aa2ac43d340be941567a76d2fe505844 ]
$B cp /system/lib/hw/copybit.msm8909.so /cache/kyf37-display-before-v6/lib/hw/copybit.msm8909.so
[ "$(hash /cache/kyf37-display-before-v6/lib/hw/copybit.msm8909.so)" = 56a5df8b26d7bf3412533dbd526fb1120db42f997a27c93ac5eeb155e62d2aef ]
$B cp /system/lib/hw/memtrack.msm8909.so /cache/kyf37-display-before-v6/lib/hw/memtrack.msm8909.so
[ "$(hash /cache/kyf37-display-before-v6/lib/hw/memtrack.msm8909.so)" = bbf47cc31d68817b0e3c07b4afb34e728dc15f5572ddf12769a2653e8e3546b4 ]
[ "$(hash /tmp/clear-system-temp-wp)" = 958575ecb6b1a4a8f6d909f22a7412adfef03861bad1782b2b3baccd7bb5b9c9 ]
$B chmod 755 /tmp/clear-system-temp-wp
/tmp/clear-system-temp-wp --clear-system-temporary > /tmp/v6-display-wp.log
$B cp /tmp/v6-display-providers/lib/liboverlay.so /system/lib/liboverlay.so
$B chmod 644 /system/lib/liboverlay.so
$B chown 0:0 /system/lib/liboverlay.so
chcon u:object_r:system_file:s0 /system/lib/liboverlay.so
[ "$(hash /system/lib/liboverlay.so)" = 3f5edf1d137ba9ee869a3a61cabf854af83889e90cb0a0e4d87527de54eba31d ]
$B cp /tmp/v6-display-providers/lib/libhdmi.so /system/lib/libhdmi.so
$B chmod 644 /system/lib/libhdmi.so
$B chown 0:0 /system/lib/libhdmi.so
chcon u:object_r:system_file:s0 /system/lib/libhdmi.so
[ "$(hash /system/lib/libhdmi.so)" = 87c7cfea41965838dcabd0bf31572aabf9d30960ef049389bf0b8ffb24549f40 ]
$B cp /tmp/v6-display-providers/lib/libqdutils.so /system/lib/libqdutils.so
$B chmod 644 /system/lib/libqdutils.so
$B chown 0:0 /system/lib/libqdutils.so
chcon u:object_r:system_file:s0 /system/lib/libqdutils.so
[ "$(hash /system/lib/libqdutils.so)" = e69243e85a60f061bf038fd0a830904de0c13d2956a62d8d5e1d303833cdd6da ]
$B cp /tmp/v6-display-providers/lib/libmemalloc.so /system/lib/libmemalloc.so
$B chmod 644 /system/lib/libmemalloc.so
$B chown 0:0 /system/lib/libmemalloc.so
chcon u:object_r:system_file:s0 /system/lib/libmemalloc.so
[ "$(hash /system/lib/libmemalloc.so)" = 3570380ac3c4baf22541a00420db94ad908bb2b482b19ad58192618efb1222e9 ]
$B cp /tmp/v6-display-providers/lib/libqdMetaData.so /system/lib/libqdMetaData.so
$B chmod 644 /system/lib/libqdMetaData.so
$B chown 0:0 /system/lib/libqdMetaData.so
chcon u:object_r:system_file:s0 /system/lib/libqdMetaData.so
[ "$(hash /system/lib/libqdMetaData.so)" = 70fc4d54581939670c117beb2a9918fdd75d3ec17fb0666bab56a3b55f37160c ]
$B cp /tmp/v6-display-providers/lib/libqservice.so /system/lib/libqservice.so
$B chmod 644 /system/lib/libqservice.so
$B chown 0:0 /system/lib/libqservice.so
chcon u:object_r:system_file:s0 /system/lib/libqservice.so
[ "$(hash /system/lib/libqservice.so)" = 803aff49e258b654090de8a0b3714cce20d66e35c5fca54bb7eb10e1f1638fe2 ]
$B cp /tmp/v6-display-providers/lib/hw/hwcomposer.msm8909.so /system/lib/hw/hwcomposer.msm8909.so
$B chmod 644 /system/lib/hw/hwcomposer.msm8909.so
$B chown 0:0 /system/lib/hw/hwcomposer.msm8909.so
chcon u:object_r:system_file:s0 /system/lib/hw/hwcomposer.msm8909.so
[ "$(hash /system/lib/hw/hwcomposer.msm8909.so)" = d5013a7173d1b229ccf6658ee3a03cffc07a8794c0085d0f23073b9daa02f269 ]
$B cp /tmp/v6-display-providers/lib/hw/gralloc.msm8909.so /system/lib/hw/gralloc.msm8909.so
$B chmod 644 /system/lib/hw/gralloc.msm8909.so
$B chown 0:0 /system/lib/hw/gralloc.msm8909.so
chcon u:object_r:system_file:s0 /system/lib/hw/gralloc.msm8909.so
[ "$(hash /system/lib/hw/gralloc.msm8909.so)" = 34cee9437c17f3c1e37dd2f68f0b2c9f234d7db6f1641f0538255d284d527bde ]
$B cp /tmp/v6-display-providers/lib/hw/copybit.msm8909.so /system/lib/hw/copybit.msm8909.so
$B chmod 644 /system/lib/hw/copybit.msm8909.so
$B chown 0:0 /system/lib/hw/copybit.msm8909.so
chcon u:object_r:system_file:s0 /system/lib/hw/copybit.msm8909.so
[ "$(hash /system/lib/hw/copybit.msm8909.so)" = cf40d5802defbad61241c49ab5a6c991f651ccc6eedf49192b9c23cf59e69454 ]
$B cp /tmp/v6-display-providers/lib/hw/memtrack.msm8909.so /system/lib/hw/memtrack.msm8909.so
$B chmod 644 /system/lib/hw/memtrack.msm8909.so
$B chown 0:0 /system/lib/hw/memtrack.msm8909.so
chcon u:object_r:system_file:s0 /system/lib/hw/memtrack.msm8909.so
[ "$(hash /system/lib/hw/memtrack.msm8909.so)" = e2c240a9d368525764df6e433a59667be29ff16d5c09cddb24d54464ca626112 ]
$B sync
echo DISPLAY_PROVIDER_CORRECTION_VERIFIED
