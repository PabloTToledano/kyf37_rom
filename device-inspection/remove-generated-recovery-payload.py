"""Between builds, remove only obsolete generated recovery payload files."""
from pathlib import Path
import subprocess
tree=Path('/home/pablo/kyf37-lineage')
board=(tree/'device/kyocera/kyf37/BoardConfig.mk').read_text()
assert 'TARGET_NO_RECOVERY := true' in board
processes=subprocess.check_output(['ps','-eo','args'],text=True)
assert not any('prebuilts/ninja/linux-x86/ninja bootimage systemimage' in x
               and not x.startswith(('ps ','bash ')) for x in processes.splitlines()),'Build is still running'
base=(tree/'out/target/product/kyf37/system').resolve()
for rel in ('bin/install-recovery.sh','etc/install-recovery.sh',
            'recovery-from-boot.p','etc/recovery-resource.dat'):
    path=base/rel
    assert path.parent.resolve().is_relative_to(base)
    if path.exists():
        assert path.is_file() and not path.is_symlink()
        path.unlink()
        print('Removed obsolete generated payload:',rel)
print('Generated recovery replacement payloads absent; TWRP maintained separately.')
