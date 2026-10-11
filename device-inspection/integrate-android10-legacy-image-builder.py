from pathlib import Path
import subprocess
tree=Path('/home/pablo/kyf37-android10')
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0
p=tree/'device/kyocera/kyf37/BoardConfig.mk';s=p.read_text()
s=s.replace('# Leave empty: some image-builder conditions use nonempty, not equality to true.','# Legacy ramdisk boot, with explicit opt-in in the Android 10 image builder.')
line='KYF37_LEGACY_SYSTEM_LAYOUT := true\n'
if line not in s:s+='\n'+line
p.write_text(s)
p=tree/'build/make/core/Makefile';s=p.read_text()
old='$(hide) echo "root_dir=$(TARGET_ROOT_OUT)" >> $(1)'
new='''$(if $(filter true,$(KYF37_LEGACY_SYSTEM_LAYOUT)),\
    $(hide) echo "system_root_image=false" >> $(1))
'''+old
if new not in s:
    assert old in s
    p.write_text(s.replace(old,new,1))
p=tree/'build/make/tools/releasetools/build_image.py';s=p.read_text()
old='  if "first_pass" in prop_dict:\n'
new='''  # Explicit legacy-system opt-in; default Android 10 staging remains unchanged.
  if prop_dict.get("system_root_image") == "false":
    return origin_in, fs_config

'''+old
if new not in s:
    assert old in s
    p.write_text(s.replace(old,new,1))
for name in ['system-android10-validated.raw.img','boot-android10-legacy-unsigned.img']:
    source=Path('/home/pablo/kyf37-rom')/name
    target=source.with_name(source.stem+'-before-legacy-builder-fix.img')
    if source.exists():
        assert not target.exists()
        source.rename(target)
print('Explicit system_root_image=false now retains legacy /system image contents. Other products keep default staging.')
