import subprocess,time,json
from pathlib import Path
adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe';out=Path(__file__).resolve().parent/'outer-animation'
def sh(c):return subprocess.check_output([adb,'-s','981108631314','shell',c]).decode(errors='replace')
def lid(x):sh('sendevent /dev/input/event8 5 0 '+str(x)+'; sendevent /dev/input/event8 0 0 0')
report={'samples':[]}
try:
 lid(0);time.sleep(.3);lid(1);time.sleep(1)
 sh('sendevent /dev/input/event2 1 254 1; sendevent /dev/input/event2 0 0 0; sleep 1.2; sendevent /dev/input/event2 1 254 0; sendevent /dev/input/event2 0 0 0')
 start=time.monotonic();time.sleep(1)
 assert 'KYF37:BadApple' in sh('dumpsys power')
 while time.monotonic()-start<230:
  elapsed=round(time.monotonic()-start,1);power=sh('dumpsys power')
  active='KYF37:BadApple' in power
  sample={'seconds':elapsed,'active':active,'main_off':'state=OFF' in power}
  report['samples'].append(sample);print(json.dumps(sample),flush=True)
  if not active:break
  time.sleep(15)
 report['completed_without_button']=not report['samples'][-1]['active'] and report['samples'][-1]['seconds']>=210
 report['main_stayed_off']=all(x['main_off'] for x in report['samples'])
 report['no_animation_lock']='KYF37:OuterAnimation' not in sh('dumpsys power')
 report['audio']=sh('dumpsys audio')
except Exception as e:
 report['error']=str(e)
finally:
 try:lid(0)
 except Exception:pass
 (out/'badapple-full-playback.json').write_text(json.dumps(report,indent=2))
(out/'badapple-full-playback.json').write_text(json.dumps(report,indent=2))
print('COMPLETE '+str(report['completed_without_button']),flush=True)
assert report['completed_without_button'] and report['main_stayed_off']
