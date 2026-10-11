"""Configure physical-only unlock/menu controls, home guide and base HAL declarations."""
from pathlib import Path
import subprocess, xml.etree.ElementTree as ET
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0
tree=Path('/home/pablo/kyf37-android10')
device=tree/'device/kyocera/kyf37'
nav=tree/'frameworks/base/services/core/java/com/android/server/policy/Kyf37Navigation.java'
s=nav.read_text()
marker='// Outside the OEM launcher, F2 supplies the standard Menu key.'
if marker not in s:
    anchor='        if (code == KeyEvent.KEYCODE_F4) {'
    assert s.count(anchor)==1
    code='''        // Outside the OEM launcher, F2 supplies the standard Menu key.
        if (code == KeyEvent.KEYCODE_F2) {
            final KeyEvent mapped = new KeyEvent(event.getDownTime(), event.getEventTime(),
                    event.getAction(), KeyEvent.KEYCODE_MENU, event.getRepeatCount(),
                    event.getMetaState(), event.getDeviceId(), event.getScanCode(),
                    event.getFlags(), event.getSource());
            handler.post(new Runnable() { public void run() {
                try { input.injectInputEvent(mapped, InputManager.INJECT_INPUT_EVENT_MODE_ASYNC); }
                finally { mapped.recycle(); }
            }});
            return true;
        }
'''
    nav.write_text(s.replace(anchor,code+anchor))
overlay=device/'overlay/frameworks/base/packages/SystemUI/res/values/kyf37_keyguard.xml'
overlay.parent.mkdir(parents=True,exist_ok=True)
overlay.write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Menu dismisses non-secure swipe or opens the credential bouncer;
         it does not bypass a PIN/password. KYF37 has no touchscreen. -->
    <bool name="config_disableMenuKeyInLockScreen">false</bool>
</resources>
''')
home=tree/'packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
s=home.read_text()
if 'F1: Settings  OK: Open' not in s:
    s=s.replace('import android.widget.TextView;', 'import android.widget.TextView;\nimport android.widget.LinearLayout;\nimport android.widget.ListView;\nimport android.view.ViewGroup;')
    anchor='        getListView().addHeaderView(title, null, false);'
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'''
        ListView list = getListView();
        ViewGroup oldParent = (ViewGroup) list.getParent();
        oldParent.removeView(list);
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.addView(list, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        TextView guide = new TextView(this);
        guide.setText("F1: Settings  OK: Open\\nF2: Menu  F3: Home  F4: Cursor");
        guide.setTextSize(12);
        guide.setTextColor(0xFFFFFFFF);
        guide.setBackgroundColor(0xFF202020);
        guide.setPadding(12, 8, 12, 8);
        screen.addView(guide, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(screen);
        list.requestFocus();''')
    home.write_text(s)
mk=device/'device.mk'
marker='# Battery HAL for the standard power-supply nodes'
if marker not in mk.read_text():
    mk.write_text(mk.read_text()+'\n'+marker+'\nPRODUCT_PACKAGES += android.hardware.health@2.0-service android.hardware.health@2.0-impl-default\n')
path=device/'manifest.xml'
manifest=ET.parse(path);root=manifest.getroot()
specs=[('android.hardware.health','2.0',[('IHealth','default')]),
       ('android.hardware.configstore','1.1',[('ISurfaceFlingerConfigs','default')]),
       ('android.hardware.cas','1.1',[('IMediaCasService','default')]),
       ('android.hardware.media.omx','1.0',[('IOmx','default'),('IOmxStore','default')]),
       ('android.hardware.media.c2','1.0',[('IComponentStore','software')])]
for name,version,interfaces in specs:
    if any(h.findtext('name')==name for h in root.findall('hal')):continue
    h=ET.SubElement(root,'hal',format='hidl')
    ET.SubElement(h,'name').text=name
    ET.SubElement(h,'transport').text='hwbinder'
    ET.SubElement(h,'version').text=version
    for interface,instance in interfaces:
        i=ET.SubElement(h,'interface')
        ET.SubElement(i,'name').text=interface
        ET.SubElement(i,'instance').text=instance
ET.indent(manifest);manifest.write(path,encoding='utf-8',xml_declaration=True)
print('Physical menu/unlock, persistent home key guide, battery and base media/config HAL declarations integrated; device testing pending.')
