import subprocess
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
s='echo "file drivers/net/wireless/wcnss/wcnss_wlan.c line 2208 +p" > /sys/kernel/debug/dynamic_debug/control; echo WCNSS_CTRL.6 > /sys/bus/platform/drivers/WCNSS_CTRL/unbind; echo WCNSS_CTRL.6 > /sys/bus/platform/drivers/WCNSS_CTRL/bind'
subprocess.run([adb,'-s','981108631314','shell',s],check=True)
