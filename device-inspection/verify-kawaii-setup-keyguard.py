"""Read-only source contract checks. Never contacts the phone or enters a PIN."""
from pathlib import Path
import xml.etree.ElementTree as ET
r=Path('/home/pablo/kyf37-android10')
sw=r/'packages/apps/SetupWizard';ui=r/'frameworks/base/packages/SystemUI'
a='{http://schemas.android.com/apk/res/android}'
w='{http://schemas.android.com/apk/res/com.google.android.setupwizard}'
script=ET.parse(sw/'res/raw/lineage_wizard_script.xml').getroot()
actions={e.get('id'):e for e in script}
assert script.get(w+'firstAction')=='welcome'
assert 'appearance' in actions
for e in actions.values():
    for result in e:
        assert result.get(w+'action') in actions
assert {e.get(w+'action') for e in actions['wifi_setup']}=={'appearance'}
assert {e.get(w+'action') for e in actions['appearance']}=={'finish'}
seen=set();at='welcome'
while at!='exit':
    assert at not in seen, 'wizard cycle'
    seen.add(at);at=next(iter(actions[at])).get(w+'action')
assert seen=={'welcome','locale','datetime','wifi_setup','appearance','finish'}
for p in ui.glob('res*/layout/keyguard_sim_pin_view.xml'):
    root=ET.parse(p).getroot();parents={c:p for p in root.iter() for c in p}
    ids={e.get(a+'id'):e for e in root.iter()}
    for digit in range(10):
        v=ids['@+id/key'+str(digit)]
        assert parents[v].get(a+'visibility')=='gone'
    for key in ['simPinEntry','key_enter','delete_button','keyguard_sim','keyguard_selector_fade_container']:
        assert '@+id/'+key in ids
    assert any(e.tag=='include' and e.get('layout')=='@layout/keyguard_eca' for e in root.iter())
for p in ui.glob('res*/layout/keyguard_clock_switch.xml'):
    assert 'Kyf37LockActions' not in p.read_text()
for p in ui.glob('res*/layout/keyguard_bottom_area.xml'):
    root=ET.parse(p).getroot();v=next(e for e in root if e.tag.endswith('Kyf37LockActions'))
    assert v.get(a+'layout_gravity')=='bottom|center_horizontal'
lock=(ui/'src/com/android/keyguard/Kyf37LockActions.java').read_text()
assert 'unlock.setBackground(null)' in lock and 'bg.setStroke' not in lock
sim=(ui/'src/com/android/keyguard/KeyguardSimPinView.java').read_text()
assert 'consume release too:' in sim
assert 'verifyPasswordAndUnlock' in sim
print('PASS: wizard graph, SIM keypad hooks/emergency layout, bottom borderless hint, Clear release')
