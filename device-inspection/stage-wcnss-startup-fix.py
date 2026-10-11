from pathlib import Path
r=Path('/home/pablo/kyf37-android10');d=r/'device/kyocera/kyf37'
# Original service uses this board's legacy data/config paths; keep CAF executable separate.
p=d/'ramdisk/init.target.rc';s=p.read_text().replace('service wcnss-service /system/bin/wcnss_service\n','service wcnss-service /system/bin/wcnss_service_stock\n');p.write_text(s)
helper='''#!/system/bin/sh
# Preserve existing device NV/calibration. Seed only the missing OEM default NV.
if [ ! -e /data/misc/wifi/WCNSS_qcom_wlan_nv.bin ]; then
    cp /system/etc/wifi/WCNSS_qcom_wlan_nv.bin /data/misc/wifi/WCNSS_qcom_wlan_nv.bin || exit 1
    chown system:wifi /data/misc/wifi/WCNSS_qcom_wlan_nv.bin
    chmod 0660 /data/misc/wifi/WCNSS_qcom_wlan_nv.bin
    restorecon /data/misc/wifi/WCNSS_qcom_wlan_nv.bin
fi
setprop ctl.start wcnss-service
# Bluetooth may advertise SMD devices before userspace triggers WCNSS.
# Retry the real platform probes; never forge readiness or bypass CBC checks.
i=0
while [ "$i" -lt 30 ]; do
    for channel in WCNSS_CTRL WLAN_CTRL; do
        for node in /sys/bus/platform/devices/$channel.*; do
            [ -e "$node" ] || continue
            if [ ! -e "$node/driver" ]; then
                echo "${node##*/}" > /sys/bus/platform/drivers/$channel/bind
            fi
        done
    done
    if [ -e /sys/bus/platform/devices/WCNSS_CTRL.6/driver ] && [ -e /sys/bus/platform/devices/WLAN_CTRL.6/driver ]; then
        exit 0
    fi
    sleep 1
    i=$((i + 1))
done
exit 1
'''
(d/'kyf37-wifi-init.sh').write_text(helper)
p=d/'device.mk';s=p.read_text();mapping='device/kyocera/kyf37/kyf37-wifi-init.sh:system/bin/kyf37-wifi-init.sh'
if mapping not in s:s+='\nPRODUCT_COPY_FILES += '+mapping+'\n';p.write_text(s)
p=d/'ramdisk/init.target.rc';s=p.read_text();marker='service kyf37-wifi-init '
if marker not in s:s+='''
# Restore legacy WCNSS initialization after /data is mounted.
on post-fs-data
    start kyf37-wifi-init

service kyf37-wifi-init /system/bin/sh /system/bin/kyf37-wifi-init.sh
    class main
    user root
    group root system wifi radio
    seclabel u:r:init:s0
    disabled
    oneshot
''';p.write_text(s)
# Existing /ueventd.rc already includes /etc/firmware; remove redundant search override.
p=d/'ramdisk/ueventd.qcom.rc';s=p.read_text().replace('\nfirmware_directories /system/etc/firmware /firmware/image\n','\n');p.write_text(s)
print('Staged actual OEM daemon and bounded real WCNSS/WLAN probe retry; hardware cold-boot verification pending.')
