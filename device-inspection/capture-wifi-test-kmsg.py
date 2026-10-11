from pathlib import Path
import subprocess
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
p=Path('device-inspection/wifi-test-last-kmsg.txt')
r=subprocess.run([adb,'-s','981108631314','shell','cat /proc/last_kmsg'],capture_output=True);p.write_bytes(r.stdout);print('saved',len(r.stdout),r.returncode)
r=subprocess.run([adb,'-s','981108631314','shell','cat /proc/cmdline; mount | head -8; ls /sys/fs/pstore'],text=True,capture_output=True);print(r.stdout)
