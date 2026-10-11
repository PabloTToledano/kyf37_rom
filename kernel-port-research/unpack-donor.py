"""Extract the pinned donor into the new experimental WSL workspace."""
from pathlib import Path
import hashlib
import json
import tarfile

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research')
archive = work / 'donor.tar.gz'
dest = work / 'kernel-3.18'
commit = '652b4259bd6f6195beda2e55c0b36a090257bcd8'
prefix = 'android_kernel_kyocera_afp-' + commit
with tarfile.open(archive, 'r:gz') as tf:
    members = tf.getmembers()
    for m in members:
        parts = Path(m.name).parts
        assert parts and parts[0] == prefix and '..' not in parts, m.name
    if not (dest / '.donor-commit').exists():
        # Preserve archive layout while extracting safely under the NEW root.
        tf.extractall(work, filter='data')
        unpacked = work / prefix
        assert not dest.exists(), 'Refusing to overwrite an existing source directory'
        unpacked.rename(dest)
        (dest / '.donor-commit').write_text(commit + '\n')
    assert (dest / '.donor-commit').read_text().strip() == commit
report = {'commit': commit, 'repository': 'saga0324/android_kernel_kyocera_afp',
          'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
          'source': str(dest), 'members': len(members)}
(root / 'donor-provenance.json').write_text(json.dumps(report, indent=2) + '\n')
print('Verified archive structure and extracted donor:', report)
