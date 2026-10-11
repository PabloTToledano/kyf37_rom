"""Windows hardware smoke test: real gpio/side-key input path and fb1 snapshots.
Hold tools/phone-lock.ps1 before running. Restores lid-open input state finally.
"""
import subprocess
import time
from pathlib import Path
import json
adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
out = Path(__file__).resolve().parent/'outer-animation'
def call(*args):
    return subprocess.run([adb,'-s','981108631314',*args],capture_output=True,check=True).stdout
def shell(cmd):return call('shell',cmd).decode(errors='replace')
def lid(closed):shell('sendevent /dev/input/event8 5 0 '+str(int(closed))+'; sendevent /dev/input/event8 0 0 0')
def press():shell('sendevent /dev/input/event2 1 254 1; sendevent /dev/input/event2 0 0 0; sendevent /dev/input/event2 1 254 0; sendevent /dev/input/event2 0 0 0')
def snap(name):
    b=call('exec-out','dd','if=/dev/graphics/fb1','bs=9216','count=1')[:9216]
    assert len(b)==9216,len(b)
    (out/(name+'.raw')).write_bytes(b)
    return b
report={}
try:
    lid(False);time.sleep(.2);lid(True);time.sleep(.4)
    press();time.sleep(.3)
    clock=snap('clock-before')
    press();time.sleep(.25)
    a=snap('animation-a');time.sleep(.3);b=snap('animation-b')
    report['frames_change']=a!=b
    report['animation_differs_from_clock']=a!=clock and b!=clock
    report['main_display_during_animation']=shell('dumpsys power | grep -E "mWakefulness=|Display Power"')
    time.sleep(4)
    after=snap('clock-after')
    report['returns_to_clock']=after==clock
    report['animation_wakelock_released']='KYF37:OuterAnimation' not in shell('dumpsys power')
    press();press();time.sleep(.25);press();time.sleep(.3)
    report['third_press_cancels']=snap('clock-cancel')==clock
    press();press();time.sleep(.2);lid(False);time.sleep(.4)
    report['opening_releases_wakelock']='KYF37:OuterAnimation' not in shell('dumpsys power')
    report['main_display_after_open']=shell('dumpsys power | grep -E "mWakefulness=|Display Power"')
finally:
    lid(False)
(out/'hardware-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert report['frames_change'] and report['animation_differs_from_clock']
assert report['returns_to_clock'] and report['third_press_cancels']
assert report['animation_wakelock_released'] and report['opening_releases_wakelock']
assert 'state=OFF' in report['main_display_during_animation']
assert 'state=ON' in report['main_display_after_open']
