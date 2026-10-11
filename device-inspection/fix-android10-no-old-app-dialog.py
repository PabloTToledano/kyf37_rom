from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/wm/AppWarnings.java')
s=p.read_text()
a='''    public void showDeprecatedTargetDialogIfNeeded(ActivityRecord r) {
'''
b='''    public void showDeprecatedTargetDialogIfNeeded(ActivityRecord r) {
        // KYF37 ships original Lollipop-era Kyocera apps; never block them with the warning.
        if ("kyf37".equals(Build.DEVICE)) return;
'''
if 'KYF37 ships original Lollipop-era' not in s:
    assert s.count(a)==1; p.write_text(s.replace(a,b))
print('ok')
