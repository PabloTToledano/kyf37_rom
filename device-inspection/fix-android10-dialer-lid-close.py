"""Native dialer lid-close call handling; rerunnable after the app generator."""
from pathlib import Path
here=Path(__file__).resolve().parent
tree=Path('/home/pablo/kyf37-android10')
base=tree/'packages/apps/Kyf37Dialer/src/org/kyf37/dialer'
def write(p,s):
    if not p.exists() or p.read_text()!=s: p.write_text(s)
write(base/'Kyf37LidCallReceiver.java',(here/'Kyf37LidCallReceiver.java.txt').read_text())
p=base/'KeitaiInCallService.java'; s=p.read_text()
anchor='    private static CallAudioState sAudio;'
if 'private final Kyf37LidCallReceiver lidReceiver' not in s:
    assert anchor in s
    s=s.replace(anchor,anchor+'\n    private final Kyf37LidCallReceiver lidReceiver = new Kyf37LidCallReceiver();')
anchor='        super.onCreate();'
if 'new android.content.IntentFilter(Kyf37LidCallReceiver.ACTION)' not in s:
    assert anchor in s
    s=s.replace(anchor,anchor+'''
        // Only the system telephony-policy sender may end calls through this receiver.
        registerReceiver(lidReceiver, new android.content.IntentFilter(Kyf37LidCallReceiver.ACTION),
                "android.permission.MODIFY_PHONE_STATE", null);
''',1)
anchor='    @Override public void onDestroy() {'
if 'unregisterReceiver(lidReceiver)' not in s:
    assert anchor in s
    s=s.replace(anchor,anchor+'\n        unregisterReceiver(lidReceiver);',1)
write(p,s)
p=base/'KUi.java'; s=p.read_text()
if 'private static String cornerActionLabel' not in s:
    anchor='        public void hints(String left, String centre, String right) {'
    assert anchor in s
    s=s.replace(anchor,'''        private static String cornerActionLabel(String label) {
            return label == null ? "" : label.replaceFirst("^(?:F[1-4]|OK|Call)\\\\s+", "");
        }
'''+anchor)
    s=s.replace('hintL.setText(left == null ? "" : left);','hintL.setText(cornerActionLabel(left));')
    s=s.replace('hintC.setText(centre == null ? "" : centre);','hintC.setText(cornerActionLabel(centre));')
write(p,s)
p=here/'build-kyf37-android10.sh'; s=p.read_text()
line='python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-dialer-lid-close.py'
anchor='python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/verify-keypad-system-polish.py'
if line not in s:
    assert anchor in s
    s=s.replace(anchor,line+'\n'+anchor)
write(p,s)
p=here/'build-locked.sh'; s=p.read_text()
anchor='elif [ "${1:-}" = "--kernel" ]; then'
if '--staged-dialer' not in s:
    assert anchor in s
    s=s.replace(anchor,'''elif [ "${1:-}" = "--staged-dialer" ]; then
    bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-staged-dialer.sh >> "$LOG" 2>&1
'''+anchor)
write(p,s)
print('Native dialer: protected lid receiver ends calls on close; app-only build mode staged')
