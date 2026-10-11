import subprocess,time,json,re
from pathlib import Path
adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
out=Path(__file__).resolve().parent/'outer-animation'
def call(*a):return subprocess.run([adb,'-s','981108631314',*a],capture_output=True,check=True).stdout
def sh(c):return call('shell',c).decode(errors='replace')
def lid(c):sh('sendevent /dev/input/event8 5 0 '+str(int(c))+'; sendevent /dev/input/event8 0 0 0')
def press():sh('sendevent /dev/input/event2 1 254 1; sendevent /dev/input/event2 0 0 0; sleep 0.08; sendevent /dev/input/event2 1 254 0; sendevent /dev/input/event2 0 0 0')
def changed(a,n):
 for _ in range(10):
  time.sleep(1.5)
  if snap(n)!=a:return True
 return False
def snap(n):
 b=call('exec-out','dd','if=/dev/graphics/fb1','bs=9216','count=1')[:9216];assert len(b)==9216
 (out/(n+'.raw')).write_bytes(b);return b
report={}
try:
 lid(False);time.sleep(.2);lid(True);time.sleep(3)
 a=snap('idle-a');report['idle_animates']=changed(a,'idle-b')
 snapshots=[]
 for i in range(4):
  press();time.sleep(1.1);snapshots.append(snap('scene-'+str(i)))
 report['every_press_new_scene']=len(set(snapshots))==4
 report['main_off']='state=OFF' in sh('dumpsys power')
 time.sleep(8)
 for _ in range(10):
  if 'KYF37:OuterAnimation' not in sh('dumpsys power'):break
  time.sleep(1.5)
 report['returns_to_idle']='KYF37:OuterAnimation' not in sh('dumpsys power')
 c=snap('idle-return');report['idle_resumes']=changed(c,'idle-resumed')
 press();time.sleep(.3);lid(False);time.sleep(.5)
 report['opening_cancels']='KYF37:OuterAnimation' not in sh('dumpsys power')
 report['opens_main']='state=ON' in sh('dumpsys power')
 report['scene_log']=sh('logcat -d -s KYF37OuterScreen:I | tail -10')
finally:lid(False)
(out/'variety-hardware-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert all(v for k,v in report.items() if k!='scene_log')
