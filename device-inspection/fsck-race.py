import subprocess,time,sys
adb=r'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
S='981108631314'
end=time.time()+float(sys.argv[1]); mode=sys.argv[2]  # -fn or -fy
cmd=("stop recovery; sync; umount /data 2>&1; umount /sdcard 2>&1; "
 "ls /sbin/e2fsck /system/bin/e2fsck 2>&1; "
 "e2fsck %s /dev/block/bootdevice/by-name/userdata > /tmp/fsck.log 2>&1; echo FSCK_RC=$?; tail -40 /tmp/fsck.log; echo UP; cat /proc/uptime"%mode)
while time.time()<end:
  try: r=subprocess.run([adb,'-s',S,'shell',cmd],capture_output=True,timeout=300)
  except subprocess.TimeoutExpired: print('timeout');continue
  if r.stdout:
    open('device-inspection/recovery-restart-capture/fsck-%s.txt'%mode,'wb').write(r.stdout);print(r.stdout.decode(errors='replace'));break
