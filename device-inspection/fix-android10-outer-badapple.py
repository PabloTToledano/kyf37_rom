#!/usr/bin/env python3
"""Run after fix-android10-outer-animation.py. Add interruptible local Bad Apple playback."""
from pathlib import Path
import shutil
w=Path(__file__).resolve().parent
app=Path.home()/'kyf37-android10/packages/apps/Kyf37OuterScreen'
s=(w/'OuterScreenService-animation.java.txt').read_text()
s=s.replace('    private AlarmManager alarms;',(w/'OuterScreenService-badapple.java.inc').read_text()+'\n    private AlarmManager alarms;')
s=s.replace('        super.onCreate();','        super.onCreate();\n        observeSideKey();')
s=s.replace('if(!visible) {stopAnimation();}','if(!visible) {sideHeld=false;handler.removeCallbacks(longSide);stopMovie();stopAnimation();}')
s=s.replace('if(animating)return;','if(animating || movie)return;')
s=s.replace('        boolean visible=closed();','        boolean visible=closed();\n        if(movie && visible) {\n            PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);\n            if(power.isInteractive())power.goToSleep(SystemClock.uptimeMillis(),PowerManager.GO_TO_SLEEP_REASON_LID_SWITCH,0);\n        }')
s=s.replace('events.addAction(Intent.ACTION_TIME_CHANGED);','events.addAction(Intent.ACTION_SCREEN_ON);events.addAction(Intent.ACTION_TIME_CHANGED);')
s=s.replace('            stopAnimation();startAnimation();return START_STICKY;','            if(!inputReady) {if(movie){stopMovie();refresh();}else{stopAnimation();startAnimation();}}\n            return START_STICKY;')
s=s.replace('        stopAnimation();unregisterReceiver','        inputRunning=false;sideHeld=false;handler.removeCallbacks(longSide);stopMovie();\n        stopAnimation();unregisterReceiver')
(app/'src/org/kyf37/subdisplay/OuterScreenService.java').write_text(s)
p=app/'controller.c';s=p.read_text();marker='/* KYF37 BadApple playback'
if marker in s:s=s[:s.index(marker)]
p.write_text(s+'\n'+(w/'outer-badapple-controller.c.txt').read_text())
p=app/'AndroidManifest.xml';s=p.read_text()
if 'android.permission.DIAGNOSTIC' not in s:s=s.replace('    <application','    <uses-permission android:name="android.permission.DIAGNOSTIC"/>\n    <application')
for permission in ('DEVICE_POWER','MODIFY_AUDIO_SETTINGS'):
    name='android.permission.'+permission
    if name not in s:s=s.replace('    <application','    <uses-permission android:name="'+name+'"/>\n    <application')
p.write_text(s)
assets=app/'assets';assets.mkdir(exist_ok=True)
for name in ('badapple.frames.gz','badapple.m4a'):shutil.copyfile(w.parent/'third-party/bad-apple/assets'/name,assets/name)
# MediaPlayer openFd requires an uncompressed audio asset.
p=app/'Android.mk';s=p.read_text()
if 'LOCAL_AAPT_FLAGS := -0 m4a' not in s:s=s.replace('LOCAL_PRIVATE_PLATFORM_APIS := true','LOCAL_PRIVATE_PLATFORM_APIS := true\nLOCAL_AAPT_FLAGS := -0 m4a')
p.write_text(s)
shutil.copyfile(app/'controller.c',w.parent/'kyf37-rom/navigation/subdisplay/controller.c')
print('Bad Apple: 800ms hold, 15fps, audio, press/lid/audio-focus cancel; DIAGNOSTIC grants passive input access')
