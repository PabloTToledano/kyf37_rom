"""Stage policy sources without changing the built/flashed ROM or live tree."""
from pathlib import Path
import hashlib,json
tree=Path('/home/pablo/kyf37-lineage')
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
stage=host/'kyf37-rom/kyocera-compat/policy-source'
stage.mkdir(parents=True,exist_ok=True)
policy=tree/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=policy.read_text()
old='        if (mKyf37Navigation != null && mKyf37Navigation.intercept(event)) return -1;'
new='''        // Preserve native launcher softkeys, while retaining Home/cursor elsewhere.
        final boolean kyf37NativeKeys = !keyguardOn && win != null
                && "jp.kyocera.afphome".equals(win.getOwningPackage());
        if (mKyf37Navigation != null
                && mKyf37Navigation.intercept(event, kyf37NativeKeys)) return -1;'''
assert s.count(old)==1
s=s.replace(old,new)
anchor=s.index('    public long interceptKeyBeforeDispatching(')
tail=s[anchor:]
old='        final int keyCode = event.getKeyCode();'
assert old in tail
tail=tail.replace(old,'''        final int keyCode = event.getKeyCode() == KeyEvent.KEYCODE_F3 && !kyf37NativeKeys
                ? KeyEvent.KEYCODE_HOME : event.getKeyCode();''',1)
s=s[:anchor]+tail
(stage/'PhoneWindowManager.java').write_text(s)
navigation=(host/'kyf37-rom/navigation/Kyf37Navigation.java').read_text()
old='    public boolean intercept(KeyEvent event) {'
new='''    public boolean intercept(KeyEvent event) {
        return intercept(event, false);
    }

    public boolean intercept(KeyEvent event, boolean nativeKeys) {
        if (nativeKeys) {
            if (enabled) reset();
            return false;
        }'''
assert navigation.count(old)==1
(stage/'Kyf37Navigation.java').write_text(navigation.replace(old,new))
layout=tree/'device/kyocera/kyf37/keylayout/matrix_keypad_67.kl'
s=layout.read_text()
import re
s,count=re.subn(r'(?m)^(key\s+61\s+)HOME\b',r'\1F3',s)
assert count==1
(stage/'matrix_keypad_67.kl').write_text(s)
report={'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir() if p.is_file()},
 'behavior':'F3/F4 reach jp.kyocera.afphome when unlocked; other windows retain F3 Home and F4 cursor.',
 'compiled':False,'applied_to_build_tree':False,'flashed':False,
 'remaining_checks':'Compile complete policy; verify keyguard, physical key press/release/repeat, Home long press and cursor cancellation on focus transition. F3 queue/wake behavior also needs review.'}
(stage/'verification.json').write_text(json.dumps(report,indent=2))
print('Staged conditional launcher key policy; not applied, compiled or flashed')
