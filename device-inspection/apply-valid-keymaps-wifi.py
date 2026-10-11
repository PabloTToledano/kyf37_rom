from pathlib import Path
import subprocess
base=Path(r'C:/Users/pablo/Documents/ChatGPT/flipphone_roms')
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
def run(*args):
 p=subprocess.run([adb,'-s','981108631314',*args],text=True,capture_output=True);print(p.stdout,p.stderr);p.check_returncode()
for p in (base/'device-inspection/keylayouts-android10-valid').glob('*.kl'):
 run('push',str(p),'/data/local/tmp/'+p.name)
 run('shell','chmod 644 /data/local/tmp/'+p.name+'; mount --bind /data/local/tmp/'+p.name+' /system/usr/keylayout/'+p.name)
for f in ['android.hardware.wifi.xml','android.hardware.wifi.direct.xml']:
 p=base/'device-inspection'/f
 subprocess.run(['wsl','-d','Ubuntu','--','cp','/home/pablo/kyf37-android10/frameworks/native/data/etc/'+f,'/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/'+f],check=True)
 run('push',str(p),'/data/local/tmp/'+f)
run('shell','mkdir -p /data/local/tmp/kyf37-permissions; cp -a /system/etc/permissions/. /data/local/tmp/kyf37-permissions/; cp /data/local/tmp/android.hardware.wifi*.xml /data/local/tmp/kyf37-permissions/; chmod 644 /data/local/tmp/kyf37-permissions/android.hardware.wifi*.xml; mount --bind /data/local/tmp/kyf37-permissions /system/etc/permissions; setprop ctl.restart zygote')
