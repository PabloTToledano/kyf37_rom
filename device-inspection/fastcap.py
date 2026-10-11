import subprocess,time,sys
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
out='device-inspection/recovery-restart-capture/'
end=time.time()+float(sys.argv[1]);n=0
cmd=("echo UP;cat /proc/uptime;cat /proc/cmdline;getprop ro.twrp.version;cat /sys/class/power_supply/battery/capacity;"
"echo KMSG;cat /proc/last_kmsg|head -c 200000;echo PSTORE;ls /sys/fs/pstore;cat /sys/fs/pstore/* 2>&1|head -c 100000;"
"echo MISC;dd if=/dev/block/bootdevice/by-name/misc bs=512 count=3 2>/dev/null|od -c|head -8;echo RLOG;tail -80 /tmp/recovery.log")
while time.time()<end:
  try:
    r=subprocess.run([adb,'-s','981108631314','shell',cmd],capture_output=True,timeout=15)
  except subprocess.TimeoutExpired: continue
  if r.stdout:
    n+=1;open(out+'cap%d.txt'%n,'wb').write(r.stdout);print('captured',n,len(r.stdout),flush=True)
    time.sleep(8)
print('end',n)
