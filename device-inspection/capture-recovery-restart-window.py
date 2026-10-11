from pathlib import Path
import subprocess,time
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
d=Path('device-inspection/recovery-restart-capture');d.mkdir(exist_ok=True)
end=time.time()+50
while time.time()<end:
 r=subprocess.run([adb,'devices'],capture_output=True,text=True,timeout=4)
 if '981108631314\t' in r.stdout:
  stamp=str(int(time.time()))
  for name,cmd in [('last-kmsg','cat /proc/last_kmsg'),('recovery-log','cat /tmp/recovery.log'),('state','cat /proc/uptime; cat /proc/cmdline; cat /sys/class/power_supply/battery/capacity; cat /sys/class/power_supply/battery/voltage_now; getprop sys.boot_completed')]:
   try:
    p=subprocess.run([adb,'-s','981108631314','shell',cmd],capture_output=True,timeout=4)
    if p.returncode==0 and p.stdout:(d/(stamp+'-'+name+'.txt')).write_bytes(p.stdout);print(name,len(p.stdout),flush=True)
   except subprocess.TimeoutExpired:pass
  if list(d.glob('*last-kmsg*')):break
 time.sleep(1)
print('Capture finished',flush=True)
