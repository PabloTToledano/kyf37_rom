"""Read-only donor triage; writes reports only beside this script."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OLD = Path('/home/pablo/kyf37-rom/kernel-android10')
NEW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'kernel-3.18'
AREAS = ['drivers/video/msm/mdss', 'drivers/gpu/msm',
         'drivers/media/platform/msm/camera_v2', 'drivers/soc/qcom',
         'drivers/char/diag', 'drivers/usb/gadget', 'sound/soc/msm',
         'drivers/staging/android', 'include/uapi/linux']
HEADERS = ['include/uapi/linux/msm_mdp.h', 'include/uapi/linux/msm_kgsl.h',
           'include/uapi/linux/ion.h', 'include/uapi/linux/msm_ion.h',
           'include/uapi/media/msm_camera.h', 'include/uapi/media/msm_cam_sensor.h']

def git(tree, *args):
    return subprocess.check_output(['git', '-C', str(tree), *args], text=True).strip()

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def files(tree, area):
    base = tree / area
    return {str(p.relative_to(tree)): digest(p) for p in base.rglob('*')
            if p.is_file() and p.suffix in ('.c', '.h', '.S')}

assert (OLD / 'Makefile').is_file() and (NEW / 'Makefile').is_file()
report = {'baseline': {'path': str(OLD), 'head': git(OLD, 'rev-parse', 'HEAD'),
                       'status': git(OLD, 'status', '--short')},
          'donor': {'path': str(NEW), 'head': git(NEW, 'rev-parse', 'HEAD') if (NEW / '.git').exists() else '652b4259bd6f6195beda2e55c0b36a090257bcd8 (pinned archive)',
                    'version': (NEW / 'Makefile').read_text().splitlines()[:5]},
          'areas': {}, 'headers': {}}
for area in AREAS:
    a, b = files(OLD, area), files(NEW, area)
    report['areas'][area] = {
        'baseline_files': len(a), 'donor_files': len(b),
        'same': sorted(p for p in a.keys() & b.keys() if a[p] == b[p]),
        'changed': sorted(p for p in a.keys() & b.keys() if a[p] != b[p]),
        'baseline_only': sorted(a.keys() - b.keys()),
        'donor_only': sorted(b.keys() - a.keys())}
for p in HEADERS:
    report['headers'][p] = {'baseline_sha256': digest(OLD / p),
                            'donor_sha256': digest(NEW / p)}
report['donor_msm8909_dts'] = sorted(str(p.relative_to(NEW)) for p in
                                     (NEW / 'arch/arm/boot/dts').rglob('*8909*'))
report['donor_defconfigs'] = sorted(p.name for p in
                                    (NEW / 'arch/arm/configs').glob('*KC*'))
(ROOT / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
print('Donor:', report['donor'])
for area, data in report['areas'].items():
    print(area, {k: len(v) if isinstance(v, list) else v for k, v in data.items()})
print('MSM8909 DT entries:', len(report['donor_msm8909_dts']))
print('Report:', ROOT / 'comparison.json')
