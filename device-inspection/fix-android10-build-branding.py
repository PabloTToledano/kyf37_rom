"""Brand the KYF37 display name without misrepresenting its signing keys."""
from pathlib import Path
import os, subprocess

root = Path('/home/pablo/kyf37-android10')
path = root/'build/make/tools/buildinfo.sh'
old = path.read_text()
anchor = 'echo "ro.build.display.id=$BUILD_DISPLAY_ID"'
replacement = '''# KYF37 owner-facing build name; retain real signing tags separately.
if [ "$TARGET_DEVICE" = "kyf37" ]; then
  BUILD_DISPLAY_ID="${BUILD_DISPLAY_ID//pablo/althia}"
  BUILD_DISPLAY_ID="${BUILD_DISPLAY_ID// test-keys/}"
fi
echo "ro.build.display.id=$BUILD_DISPLAY_ID"'''
if '# KYF37 owner-facing build name' not in old:
    assert old.count(anchor) == 1
    path.write_text(old.replace(anchor, replacement))
print('KYF37 build display branding staged: althia, no test-keys suffix')
env = dict(os.environ, TARGET_DEVICE='kyf37', BUILD_DISPLAY_ID='lineage_kyf37-userdebug 10 QQ3A.200805.001 eng.pablo.20261011.090851 test-keys', BUILD_VERSION_TAGS='test-keys', DATE='date')
properties = dict(line.split('=', 1) for line in subprocess.check_output(['bash', str(path)], env=env, text=True).splitlines() if '=' in line)
assert properties['ro.build.display.id'] == 'lineage_kyf37-userdebug 10 QQ3A.200805.001 eng.althia.20261011.090851'
assert properties['ro.build.tags'] == 'test-keys'
print('PASS: generated display name and unchanged actual signing tags')
