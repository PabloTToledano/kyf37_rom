"""Snapshot the working kernel into an independent backport workspace."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
source = Path('/home/pablo/kyf37-rom/kernel-android10')
target = work / 'kernel'
build = work / 'build'
work.mkdir(parents=True, exist_ok=True)
if not target.exists():
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git'))
    baseline = {
        'source': str(source),
        'head': subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
        'files': {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in target.rglob('*') if p.is_file()},
    }
    (work / 'baseline-manifest.json').write_text(json.dumps(baseline, indent=2) + '\n')
    subprocess.run(['git', 'init', str(target)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git', '-C', str(target), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(target), '-c', 'user.name=KYF37 kernel backports',
                    '-c', 'user.email=kyf37@localhost', 'commit', '-m',
                    'Snapshot hardware-working KYF37 Android 10 kernel including local backports'],
                   check=True, stdout=subprocess.DEVNULL)
build.mkdir(exist_ok=True)
if not (build / '.config').exists():
    shutil.copyfile('/home/pablo/kyf37-rom/kernel-android10-gcc48-build/.config', build / '.config')
for name, old in [('core-ctl', '/home/pablo/kyf37-rom/core-ctl-reference'),
                  ('wlan', '/home/pablo/kyf37-rom/wlan-prima-caf-123')]:
    new = work / name
    if not new.exists():
        shutil.copytree(old, new, ignore=shutil.ignore_patterns('.git', '*.o', '*.ko', '*.cmd',
                         'Module.symvers', 'modules.order', '.tmp_versions'))
print('Isolated baseline and external module sources:', work)
