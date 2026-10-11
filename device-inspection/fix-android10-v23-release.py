"""Rerunnable v23 packaging support; retain all existing release gates."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
p = root/'device-inspection/build-twrp-android10-installer.py'
s = p.read_text()
s = s.replace("'v20','v22')", "'v20','v22','v23')")
s = s.replace("if revision=='v22':", "if revision in ('v22','v23'):")
s = s.replace("root/'kyf37-rom/v22-theme-validation.json'", "root/('kyf37-rom/'+revision+'-theme-validation.json')")
s = s.replace("'reports/v22-theme-validation.json'", "'reports/'+revision+'-theme-validation.json'")
anchor = "assert not output.exists()"
if "v23-keypad.zip" not in s:
    s = s.replace(anchor, "if revision=='v23':\n    output=root/'kyf37-rom/kyf37-android10-go-20261007-twrp-v23-keypad.zip'\n"+anchor)
anchor = "script=(root/'device-inspection/twrp-android10-update-binary.sh').read_text()"
if "# v23 installed display-fixed recovery" not in s:
    s = s.replace(anchor, anchor+"\nif revision=='v23': # v23 installed display-fixed recovery\n    script=script.replace('RECOVERY_HASH=9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e', 'RECOVERY_HASH=c7f5a41565595607a10930ddb174f9755568c01156a6440c34abdb5cca25141d')")
if p.read_text() != s: p.write_text(s)
p = root/'device-inspection/verify-keypad-system-artifacts.py'
s = p.read_text()
if '\nimport sys\n' not in s: s = s.replace('import zipfile', 'import zipfile\nimport sys')
s = s.replace("log = Path('/home/pablo/keypad-system-polish-staged-final3.log')", "log = Path(sys.argv[1] if len(sys.argv)>1 else '/home/pablo/keypad-system-polish-staged-final3.log')")
if p.read_text() != s: p.write_text(s)
p = root/'device-inspection/verify-v22-theme.py'
s = p.read_text()
s = s.replace('import io, json, zipfile, hashlib, sys, sys', 'import io, json, zipfile, hashlib, sys')
if 'import io, json, zipfile, hashlib, sys' not in s:
    s = s.replace('import io, json, zipfile, hashlib', 'import io, json, zipfile, hashlib, sys')
s = s.replace("art = root/'kyf37-rom/kyocera-classic'", "revision = sys.argv[1] if len(sys.argv)>1 else 'v22'\nassert revision in ('v22','v23')\nart = root/'kyf37-rom/kyocera-classic'") if 'revision = sys.argv' not in s else s
s = s.replace("'source':'final v22 build APKs'", "'source':'final '+revision+' build APKs'")
s = s.replace("root/'kyf37-rom/v22-theme-validation.json'", "root/('kyf37-rom/'+revision+'-theme-validation.json')")
if p.read_text() != s: p.write_text(s)
