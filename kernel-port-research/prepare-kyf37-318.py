"""Prepare an experimental KYF37 board/config port in a NEW WSL directory.

Run under WSL. Existing source and effective config are read only. This is a
compile-stage port, not a claim of hardware or vendor-ABI compatibility.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
WORK = Path('/home/pablo/kyf37-kernel-port-research')
NEW = WORK / 'kernel-3.18'
OLD = Path('/home/pablo/kyf37-rom/kernel-android10')
CONFIG = Path('/home/pablo/kyf37-rom/kernel-android10-gcc48-build/.config')
assert NEW.is_dir() and NEW.resolve().is_relative_to(WORK.resolve())
assert 'PATCHLEVEL = 18' in (NEW / 'Makefile').read_text()
SRC_DT = OLD / 'arch/arm/boot/dts'
DEST_DT = NEW / 'arch/arm/boot/dts/qcom/kyf37'
DEST_DT.mkdir(parents=True, exist_ok=True)
tops = ['qcom/msm8909-pm8916-qrd-skut-evt.dts',
        'qcom/msm8909-pm8916-qrd-skut-dvt.dts']
visited = {}

def copy_dt(path):
    path = path.resolve()
    assert path.is_relative_to(SRC_DT.resolve()), path
    if path in visited:
        return
    data = path.read_text()
    rel = path.relative_to(SRC_DT)
    visited[path] = {'path': str(rel),
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    for name in re.findall(r'^\s*#include\s+"([^"]+)"', data, re.M):
        copy_dt(path.parent / name)
    dest = DEST_DT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(data)

for name in tops:
    copy_dt(SRC_DT / name)
makefile = NEW / 'arch/arm/boot/dts/qcom/Makefile'
start = '# BEGIN ISOLATED KYF37 PORT\n'
end = '# END ISOLATED KYF37 PORT\n'
text = makefile.read_text()
if start in text:
    a = text.index(start)
    b = text.index(end, a) + len(end)
    text = text[:a] + text[b:]
text += '\n' + start
text += 'dtb-$(CONFIG_ARCH_MSM8909) += ' + ' '.join(
    'kyf37/' + name.replace('.dts', '.dtb') for name in tops) + '\n' + end
makefile.write_text(text)

# Retain the donor's defaults for new features, then use the effective KYF37
# settings for symbols actually declared by this kernel. olddefconfig resolves
# changed dependencies; missing/changed requirements remain visible in reports.
symbols = set()
for p in NEW.rglob('Kconfig*'):
    if p.is_file():
        symbols.update(re.findall(r'^\s*(?:menuconfig|config)\s+(\w+)',
                                 p.read_text(errors='replace'), re.M))

def parse_config(data):
    values = {}
    for line in data.splitlines():
        m = re.match(r'(?:CONFIG_(\w+)=(.*)|# CONFIG_(\w+) is not set)$', line)
        if m:
            values[m[1] or m[3]] = m[2] if m[1] else 'n'
    return values

donor = parse_config((NEW / 'arch/arm/configs/90234KC_defconfig').read_text())
old = parse_config(CONFIG.read_text())
merged = dict(donor)
merged.update({k: v for k, v in old.items() if k in symbols})
merged.update({'LOCALVERSION': '"-kyf37-port318"',
               'LOCALVERSION_AUTO': 'n', 'IKCONFIG': 'y', 'IKCONFIG_PROC': 'y',
               'ANDROID_BINDER_DEVICES': '"binder,hwbinder,vndbinder"',
               'ANDROID_BINDER_IPC_32BIT': 'y'})
defconfig = NEW / 'arch/arm/configs/KYF37_port_defconfig'
defconfig.write_text(''.join('# CONFIG_' + k + ' is not set\n' if v == 'n'
                             else 'CONFIG_' + k + '=' + v + '\n'
                             for k, v in sorted(merged.items())))
report = {
    'stage': 'experimental board and config translation, hardware untested',
    'source': str(OLD), 'destination': str(NEW),
    'baseline_config_sha256': hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
    'board_files': list(visited.values()),
    'enabled_baseline_symbols_missing_in_donor':
        {k: v for k, v in old.items() if k not in symbols and v != 'n'},
    'note': 'Copied legacy board bindings require review against 3.18 drivers. '
            'No old driver code, module binaries, or signing key copied.'}
(ROOT / 'port-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
print('Prepared', defconfig, 'and', len(visited), 'board files')
print('Enabled baseline symbols absent from donor:',
      len(report['enabled_baseline_symbols_missing_in_donor']))
