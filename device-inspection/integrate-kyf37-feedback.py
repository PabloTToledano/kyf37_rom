"""Apply only between ROM builds; preserve OEM UI recordings and policy hooks."""
from pathlib import Path
import argparse,shutil,subprocess,json,hashlib
parser=argparse.ArgumentParser()
parser.add_argument('--tree',default='/home/pablo/kyf37-lineage')
args=parser.parse_args()
tree=Path(args.tree)
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
processes=subprocess.check_output(['ps','-eo','args'],text=True)
assert not any('ninja bootimage systemimage' in line for line in processes.splitlines()),'Build is active'
p=tree/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
if '// KYF37 original feedback integration' not in s:
    pairs=[
      ('    Context mContext;','    Context mContext;\n    // KYF37 original feedback integration\n    Kyf37Feedback mKyf37Feedback;'),
      ('        mHandler = new PolicyHandler();','        mHandler = new PolicyHandler();\n        if (SystemProperties.getBoolean("ro.kyf37.keypad_navigation", false)) {\n            mKyf37Feedback = new Kyf37Feedback(context, mHandler);\n            mKyf37Feedback.userChanged(UserHandle.USER_SYSTEM);\n        }'),
      ('    public void setCurrentUserLw(int newUserId) {',
       '    public void setCurrentUserLw(int newUserId) {\n        if (mKyf37Feedback != null) mKyf37Feedback.userChanged(newUserId);'),
      ('        final boolean interactive = (policyFlags & FLAG_INTERACTIVE) != 0;',
       '        final boolean interactive = (policyFlags & FLAG_INTERACTIVE) != 0;\n        if (mKyf37Feedback != null && (policyFlags & FLAG_INJECTED) == 0)\n            mKyf37Feedback.key(event, interactive);'),
      ('        mLidState = newLidState;',
       '        mLidState = newLidState;\n        if (mKyf37Feedback != null) mKyf37Feedback.lidChanged(lidOpen);')]
    for old,new in pairs:
        assert s.count(old)==1,(old,s.count(old))
        s=s.replace(old,new,1)
    p.write_text(s)
shutil.copy2(host/'kyf37-rom/navigation/Kyf37Feedback.java',p.parent/'Kyf37Feedback.java')
device=tree/'device/kyocera/kyf37'
mk=device/'device.mk'
text=mk.read_text()
root_start=device/'init.qcom.rootagent.sh'
shutil.copy2(host/'device-inspection/init.qcom.rootagent.sh',root_start)
root_entry='device/kyocera/kyf37/init.qcom.rootagent.sh:system/etc/init.qcom.rootagent.sh'
if root_entry not in text:text+='\nPRODUCT_COPY_FILES += '+root_entry+'\n'
shutil.copy2(host/'device-inspection/enable-rom-app-root.sh',device/'enable-rom-app-root.sh')
helper_entry='device/kyocera/kyf37/enable-rom-app-root.sh:system/etc/enable-rom-app-root.sh'
if helper_entry not in text:text+='\nPRODUCT_COPY_FILES += '+helper_entry+'\n'
hashes={}
sound_entries=[]
for audio in sorted(Path('/home/pablo/kyf37-rom/stock-system/media/audio/ui').iterdir()):
    if not audio.is_file():continue
    target=device/'audio/ui'/audio.name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(audio,target)
    entry='device/kyocera/kyf37/audio/ui/'+audio.name+':system/media/audio/ui/'+audio.name
    sound_entries.append(entry)
    assert audio.read_bytes()==target.read_bytes()
    hashes[audio.name]=hashlib.sha256(target.read_bytes()).hexdigest()
marker='# KYF37 OEM audio takes precedence over inherited AOSP audio'
if marker not in text:
    text+='\n'+marker+'\nPRODUCT_COPY_FILES := '+' '.join(sound_entries)+' $(PRODUCT_COPY_FILES)\n'
mk.write_text(text)
# Device inherits after full_base_telephony in the top product, so its own
# prepend cannot outrank the ancestor's audio. Prepend at the product root.
product=device/'lineage.mk'
product_text=product.read_text()
if marker not in product_text:
    product_text+='\n'+marker+'\nPRODUCT_COPY_FILES := '+' '.join(sound_entries)+' $(PRODUCT_COPY_FILES)\n'
    product.write_text(product_text)
(host/'kyf37-rom/stock-ui-sound-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('Integrated OEM feedback source/hooks and byte-identical UI recordings.')
