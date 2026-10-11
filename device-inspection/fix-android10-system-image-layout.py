from pathlib import Path
import subprocess
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0
p=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/BoardConfig.mk')
s=p.read_text()
old='BOARD_BUILD_SYSTEM_ROOT_IMAGE := false'
new='# Leave empty: some image-builder conditions use nonempty, not equality to true.\nBOARD_BUILD_SYSTEM_ROOT_IMAGE :='
if new not in s:
    assert old in s
    p.write_text(s.replace(old,new,1))
for name in ['system-android10-validated.raw.img','boot-android10-legacy-unsigned.img']:
    source=Path('/home/pablo/kyf37-rom')/name
    target=source.with_name(source.stem+'-before-layout-fix.img')
    if source.exists():
        assert not target.exists()
        source.rename(target)
print('Legacy system image flag cleared; previous validation inputs retained as before-layout-fix artifacts.')
