"""Install the wpa_supplicant HIDL service rc + vendor wifi config (previously missing). Idempotent; WSL."""
from pathlib import Path
d = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
(d/'init.kyf37.wifi.rc').write_text('''# Wi-Fi supplicant for Android 10 (HIDL). Binary: /vendor/bin/hw/wpa_supplicant
on post-fs-data
    mkdir /data/vendor/wifi 0771 wifi wifi
    mkdir /data/vendor/wifi/wpa 0770 wifi wifi
    mkdir /data/vendor/wifi/wpa/sockets 0770 wifi wifi
    mkdir /data/vendor/wifi/hostapd 0770 wifi wifi
    mkdir /data/vendor/wifi/hostapd/ctrl 0770 wifi wifi

service wpa_supplicant /vendor/bin/hw/wpa_supplicant -O/data/vendor/wifi/wpa/sockets -puse_p2p_group_interface=1 -dd -g@android:wpa_wlan0
    interface android.hardware.wifi.supplicant@1.0::ISupplicant default
    interface android.hardware.wifi.supplicant@1.1::ISupplicant default
    interface android.hardware.wifi.supplicant@1.2::ISupplicant default
    socket wpa_wlan0 dgram 660 wifi wifi
    class main
    disabled
    oneshot
''')
(d/'wpa_supplicant.conf').write_text('ctrl_interface=wlan0\nupdate_config=1\nwowlan_triggers=any\n')
(d/'wpa_supplicant_overlay.conf').write_text('disable_scan_offload=1\n')
(d/'p2p_supplicant_overlay.conf').write_text('disable_scan_offload=1\n')
p = d/'device.mk'; s = p.read_text()
add = '''
PRODUCT_COPY_FILES += device/kyocera/kyf37/init.kyf37.wifi.rc:system/etc/init/init.kyf37.wifi.rc
'''
if 'init.kyf37.wifi.rc' not in s: p.write_text(s.rstrip()+'\n'+add)
print('ok')
