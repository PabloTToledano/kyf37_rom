"""Host gate for repeatable UI staging and valid, non-duplicated layout XML."""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
root = Path('/home/pablo/kyf37-android10/frameworks/base')
here = Path(__file__).resolve().parent
files = [root/'core/java/android/app/Activity.java',
         root/'core/java/android/app/Kyf37SystemKeyGuide.java',
         root/'services/core/java/com/android/server/policy/Kyf37Navigation.java',
         root/'packages/SystemUI/res/layout/status_bar.xml',
         root/'packages/SystemUI/res/layout/status_bar_expanded.xml',
         root/'packages/SystemUI/res/values/dimens.xml',
         root/'packages/SystemUI/src/com/android/systemui/statusbar/phone/Kyf37KeitaiKeys.java',
         root/'packages/SystemUI/src/com/android/systemui/statusbar/phone/Kyf37KeitaiGuide.java',
         here/'kyocera-port/Kyf37SoftkeyBridge.java',
         root/'services/core/java/com/android/server/policy/PhoneWindowManager.java',
         root/'services/core/java/com/android/server/policy/Kyf37QuickKeys.java']
for module,pkg in [('Kyf37Dialer','dialer'),('Kyf37Messages','messages'),('Kyf37Contacts','contacts')]:
    files.append(root.parents[1]/('packages/apps/'+module+'/src/org/kyf37/'+pkg+'/KUi.java'))
before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in files]
for name in ['native-guide-polish','keypad-system-polish']:
    subprocess.run([sys.executable,str(here/('fix-android10-'+name+'.py'))],check=True)
assert before == [(p.read_bytes(),p.stat().st_mtime_ns) for p in files], 'UI staging is not idempotent'
for p in files:
    if p.suffix == '.xml': ET.parse(p)
layout = ET.parse(files[4]).getroot()
guides = list(layout.iter('com.android.systemui.statusbar.phone.Kyf37KeitaiGuide'))
assert len(guides)==1,'Exactly one shade guide must survive older staging scripts'
android = '{http://schemas.android.com/apk/res/android}'
for node in layout.iter():
    if node.get(android+'id') in ('@+id/qs_frame','@+id/notification_stack_scroller'):
        assert node.get(android+'layout_marginBottom')=='44dp','Shade content can overlap key hints'
print('KEYPAD_SYSTEM_POLISH_HOST_GATE_OK: idempotence and XML layout structure; hardware behavior untested')
