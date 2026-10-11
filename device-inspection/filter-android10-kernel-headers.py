"""Keep device UAPI without shadowing Android 10's standard userspace headers.

Only generated headers inside the Android build output are modified. Kernel
source, implementation and the original installed header set remain untouched.
"""
from pathlib import Path
import argparse, json
parser = argparse.ArgumentParser()
parser.add_argument('include_dir',type=Path)
args = parser.parse_args()
tree = Path('/home/pablo/kyf37-android10')
directory = args.include_dir.resolve()
assert directory.is_relative_to((tree/'out').resolve()), directory
assert directory.parts[-2:] == ('usr','include'), directory
platform = tree/'bionic/libc/kernel/uapi'
legacy = {'linux/ion.h', 'linux/msm_ion.h', 'linux/msm_mdp.h', 'linux/msm_kgsl.h'}
removed, kept = [], []
for path in sorted(directory.rglob('*.h')):
    relative = path.relative_to(directory).as_posix()
    if relative not in legacy and (platform/relative).is_file():
        path.unlink()
        removed.append(relative)
    else:
        kept.append(relative)
(directory.parent/'kyf37-header-filter.json').write_text(json.dumps({'removed_platform_duplicates':removed,
    'preserved_device_headers':kept,'legacy_ioctl_overrides':sorted(legacy)},indent=2)+'\n')
print('Kernel UAPI filter: preserved',len(kept),'device headers; standard',len(removed),'headers supplied by Android 10 bionic.')
