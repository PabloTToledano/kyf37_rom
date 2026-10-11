from pathlib import Path
import argparse,shutil
parser=argparse.ArgumentParser()
parser.add_argument('--tree',default='/home/pablo/kyf37-lineage')
args=parser.parse_args()
tree=Path(args.tree)
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
p=tree/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
helper='''    // KYF37 outer display lid integration
    private void publishKyf37LidState() {
        if (!SystemProperties.getBoolean("ro.kyf37.outer_screen", false)) return;
        final String state = mLidState == LID_CLOSED ? "false" : "true";
        if (state.equals(SystemProperties.get("sys.kyf37.lid_open"))) return;
        SystemProperties.set("sys.kyf37.lid_open", state);
        if (!SystemProperties.getBoolean("sys.boot_completed", false)) return;
        mHandler.post(new Runnable() {
            @Override public void run() {
                Intent service = new Intent();
                service.setComponent(new ComponentName("org.kyf37.subdisplay",
                        "org.kyf37.subdisplay.OuterScreenService"));
                mContext.startServiceAsUser(service, UserHandle.SYSTEM);
            }
        });
    }

'''
if '// KYF37 outer display lid integration' not in s:
 anchor='    void readLidState() {'
 assert s.count(anchor)==1
 s=s.replace(anchor,helper+anchor)
 for line in ('        mLidState = mWindowManagerFuncs.getLidState();',
              '        mLidState = newLidState;'):
  assert s.count(line)==1
  s=s.replace(line,line+'\n        publishKyf37LidState();')
 p.write_text(s)
shutil.copytree(host/'kyf37-rom/navigation/subdisplay',
                tree/'packages/apps/Kyf37OuterScreen',dirs_exist_ok=True)
print('Integrated initial outer screen service and model-only lid publication.')
