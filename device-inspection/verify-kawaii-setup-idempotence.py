from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-android10');sw=r/'packages/apps/SetupWizard';ui=r/'frameworks/base/packages/SystemUI'
paths=[sw/x for x in ['res/values/colors.xml','res/values/kyf37_setup.xml','res/drawable/kyf37_bunny.xml','res/layout/welcome_activity.xml','res/layout/finish_activity.xml','res/layout/kyf37_appearance.xml','res/raw/lineage_wizard_script.xml','AndroidManifest.xml','src/org/lineageos/setupwizard/Kyf37AppearanceActivity.java']]
paths += [ui/x for x in ['res/values/kyf37_keypad_hints.xml','src/com/android/keyguard/KeyguardSimPinView.java','src/com/android/keyguard/Kyf37LockActions.java']]
for pattern in ['res*/layout/keyguard_sim_pin_view.xml','res*/layout/keyguard_clock_switch.xml','res*/layout/keyguard_bottom_area.xml']:paths += list(ui.glob(pattern))
before={p:p.read_bytes() for p in paths}
subprocess.run(['python3','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-kawaii-setup-keyguard.py'],check=True)
changed=[str(p) for p in paths if p.read_bytes()!=before[p]]
assert not changed,changed
print('PASS: patch rerun is byte-identical across',len(paths),'managed sources')
