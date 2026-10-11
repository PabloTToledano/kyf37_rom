import subprocess,time,json
from pathlib import Path
adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
out=Path(__file__).resolve().parent/'outer-animation';report={}
def call(*args):return subprocess.run([adb,'-s','981108631314',*args],check=True,capture_output=True).stdout
def sh(c):return call('shell',c).decode(errors='replace')
def lid(closed):sh('sendevent /dev/input/event8 5 0 '+str(int(closed))+'; sendevent /dev/input/event8 0 0 0')
def press(duration=.08):sh('sendevent /dev/input/event2 1 254 1; sendevent /dev/input/event2 0 0 0; sleep '+str(duration)+'; sendevent /dev/input/event2 1 254 0; sendevent /dev/input/event2 0 0 0')
def snap(name):
 b=call('exec-out','dd','if=/dev/graphics/fb1','bs=9216','count=1')[:9216];assert len(b)==9216
 (out/(name+'.raw')).write_bytes(b);return b
capture=out/'badapple-live-events.txt'
logfile=capture.open('wb')
logger=subprocess.Popen([adb,'-s','981108631314','logcat','-T','1','-s','KYF37OuterScreen:I'],stdout=logfile,stderr=subprocess.DEVNULL)
def log():return capture.read_text(errors='replace')
try:
 lid(False);time.sleep(.5);lid(True);time.sleep(2)
 press();time.sleep(.2);report['short_scene']='KYF37:OuterAnimation' in sh('dumpsys power')
 press(1.2);time.sleep(1)
 report['hold_starts_video']='KYF37:BadApple' in sh('dumpsys power')
 pid=sh('pidof org.kyf37.subdisplay').strip()
 audio=sh('dumpsys audio')
 report['audio_started']=any(('u/pid:1000/'+pid+' ') in line and 'state:started' in line and 'USAGE_MEDIA' in line for line in audio.splitlines())
 pcm=sh('cat /proc/asound/card0/pcm0p/sub0/status')
 report['pcm_running']='state: RUNNING' in pcm
 (out/'badapple-pcm-running.txt').write_text(pcm)
 mixer=sh("/data/local/tmp/tinymix-kyf37 'SPK DAC Switch'")
 (out/'badapple-speaker-mixer.txt').write_text(mixer)
 report['scene_interrupted']='KYF37:OuterAnimation' not in sh('dumpsys power')
 report['main_off']='state=OFF' in sh('dumpsys power')
 a=snap('badapple-a');time.sleep(1);b=snap('badapple-b');report['video_moves']=a!=b
 (out/'badapple-audio-active.txt').write_text(sh('dumpsys audio'))
 report['movie_wakelock']='KYF37:BadApple' in sh('dumpsys power')
 sh('input keyevent 224');time.sleep(1)
 report['closed_movie_rejects_main_wake']='state=OFF' in sh('dumpsys power') and 'KYF37:BadApple' in sh('dumpsys power')
 press();time.sleep(.4)
 report['single_press_stops']='KYF37:BadApple' not in sh('dumpsys power')
 c=snap('badapple-clock-return');report['clock_return']=c!=b
 stopped=sh('dumpsys audio');(out/'badapple-audio-stopped.txt').write_text(stopped)
 report['audio_released']=not any(('u/pid:1000/'+pid+' ') in line and 'state:started' in line and 'USAGE_MEDIA' in line for line in stopped.splitlines())
 # Stopping with a hold must not restart the movie when the same press crosses 800ms.
 press(1.2);time.sleep(.2);press(1.2);time.sleep(.4)
 report['held_stop_does_not_restart']='KYF37:BadApple' not in sh('dumpsys power')
 press(1.2);time.sleep(.3);lid(False);time.sleep(.5)
 report['lid_cancels']='KYF37:BadApple' not in sh('dumpsys power')
 report['main_opens']='state=ON' in sh('dumpsys power')
 report['events']=log()
finally:
 lid(False);logger.terminate();logger.wait(timeout=5);logfile.close()
(out/'badapple-hardware-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert all(v for k,v in report.items() if k!='events')
