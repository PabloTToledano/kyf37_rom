"""Fake Telecom call only; requires the exclusive phone lock and debug test line."""
import subprocess,time,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
lock=json.loads((root/'.phone.lock').read_text())
assert lock['owner']=='keypad-v23-install'
adb=[r'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe','-s','981108631314']
dest=root/'device-inspection/keypad-ui-validation/v23-live'
def shell(s): return subprocess.check_output(adb+['shell',s],text=True)
def calls():
    text=shell('dumpsys telecom')
    return text.split('  mCalls: ',1)[1].split('  mCallAudioManager:',1)[0].strip()
def lid(closed):
    shell('sendevent /dev/input/event8 5 0 '+str(int(closed))+'; sendevent /dev/input/event8 0 0 0')
assert not calls(),'Do not test while any real or fake call exists'
report={'fake_telecom_line':True,'physical_user_lid_test':False}
try:
    lid(False)
    shell("am broadcast -a org.kyf37.dialer.DEBUG_INCOMING --es number 5550100 -n 'org.kyf37.dialer/.TestConnectionService$Debug'")
    time.sleep(1)
    before=calls(); assert 'RINGING' in before and 'TestConnectionService' in before,before
    shell('input keyevent KEYCODE_DPAD_CENTER')
    time.sleep(1)
    active=calls(); assert 'ACTIVE' in active and 'TestConnectionService' in active,active
    (dest/'active-call.png').write_bytes(subprocess.check_output(adb+['exec-out','screencap','-p']))
    lid(True); time.sleep(1)
    after=calls(); assert not after,after
    report.update(active_call_before_close=active,call_list_after_close=after,active_close_passed=True)
finally:
    shell("am broadcast -a org.kyf37.dialer.DEBUG_REMOTE_HANGUP -n 'org.kyf37.dialer/.TestConnectionService$Debug'")
    lid(False)
(dest/'dialer-lid-live.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: fake call answered with OK; lid close ended it; lid reopened')
