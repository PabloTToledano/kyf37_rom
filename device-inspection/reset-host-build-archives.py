from pathlib import Path
root=Path('/home/pablo/kyf37-twrp/out/host/linux-x86').resolve()
assert str(root)=='/home/pablo/kyf37-twrp/out/host/linux-x86'
files=list(root.rglob('*.a'))+list(root.rglob('policy_parse.o'))
for path in files:
    assert path.resolve().is_relative_to(root)
    path.unlink()
print('Removed',len(files),'generated host archives/parser objects for rebuild')
