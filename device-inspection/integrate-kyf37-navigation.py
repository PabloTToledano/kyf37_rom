from pathlib import Path
import shutil,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--tree',default='/home/pablo/kyf37-lineage')
args=parser.parse_args()
root=Path(args.tree);host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/navigation')
p=root/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
if '// KYF37 physical navigation integration' not in s:
 pairs=[('    Context mContext;', '    Context mContext;\n    // KYF37 physical navigation integration\n    Kyf37Navigation mKyf37Navigation;'),
 ('        mHandler = new PolicyHandler();','        mHandler = new PolicyHandler();\n        if (SystemProperties.getBoolean("ro.kyf37.keypad_navigation", false)) {\n            mKyf37Navigation = new Kyf37Navigation(context, mHandler);\n        }'),
 ('        final boolean keyguardOn = keyguardOn();','        final boolean keyguardOn = keyguardOn();\n        if (mKyf37Navigation != null && mKyf37Navigation.intercept(event)) return -1;'),
 ('    public void finishedGoingToSleep(int why) {','    public void finishedGoingToSleep(int why) {\n        if (mKyf37Navigation != null) mKyf37Navigation.reset();'),
 ('    public void notifyLidSwitchChanged(long whenNanos, boolean lidOpen) {','    public void notifyLidSwitchChanged(long whenNanos, boolean lidOpen) {\n        if (!lidOpen && mKyf37Navigation != null) mKyf37Navigation.reset();')]
 for old,new in pairs:
  assert s.count(old)==1,old
  s=s.replace(old,new,1)
 p.write_text(s)
# This hook is separately idempotent for trees integrated before it was added.
old='    public void setCurrentUserLw(int newUserId) {'
new=old+'\n        if (mKyf37Navigation != null) mKyf37Navigation.reset();'
if new not in s:
 assert s.count(old)==1,old
 s=s.replace(old,new,1)
 p.write_text(s)
shutil.copy2(host/'Kyf37Navigation.java',p.parent/'Kyf37Navigation.java')
shutil.copytree(host/'ime',root/'packages/inputmethods/Kyf37KeypadIME',dirs_exist_ok=True)
print('Installed framework navigation and keypad IME sources')

shutil.copytree(host/'home',root/'packages/apps/Kyf37Home',dirs_exist_ok=True)
