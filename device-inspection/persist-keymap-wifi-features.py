import subprocess
from pathlib import Path
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
def sh(s):
 p=subprocess.run([adb,'-s','981108631314','shell',s],text=True,capture_output=True);print(p.stdout,p.stderr);p.check_returncode()
sh('mkdir -p /data/local/tmp/kyf37-keymap-wifi-backup; mount -o remount,rw /system')
try:
 for p in Path('device-inspection/keylayouts-android10-valid').glob('*.kl'):
  f=p.name
  sh('umount /system/usr/keylayout/'+f+'; cp -p /system/usr/keylayout/'+f+' /data/local/tmp/kyf37-keymap-wifi-backup/'+f+'; cp /data/local/tmp/'+f+' /system/usr/keylayout/'+f+'; chmod 644 /system/usr/keylayout/'+f+'; restorecon /system/usr/keylayout/'+f)
 sh('umount /system/etc/permissions; cp /data/local/tmp/android.hardware.wifi.xml /system/etc/permissions/; cp /data/local/tmp/android.hardware.wifi.direct.xml /system/etc/permissions/; chmod 644 /system/etc/permissions/android.hardware.wifi*.xml; restorecon /system/etc/permissions/android.hardware.wifi*.xml; sync')
finally:sh('mount -o remount,ro /system')
sh('sha256sum /system/usr/keylayout/qpnp_pon.kl /system/usr/keylayout/matrix_keypad_67.kl; pm list features | grep wifi')
