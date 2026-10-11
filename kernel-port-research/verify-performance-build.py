"""Audit the finished isolated build, modules, source preservation and outputs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import re

root = Path(__file__).resolve().parent
workspace = root.parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
kernel, build = work / 'kernel', work / 'build'
candidate = root / 'performance-candidate'
candidate.mkdir(exist_ok=True)
old_modules = Path('/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary/lib/modules')
modules = candidate / 'modules'
modules.mkdir(exist_ok=True)
rebuilt = {p.name: p for p in build.rglob('*.ko')}
rebuilt['core_ctl.ko'] = work / 'core-ctl/core_ctl.ko'
rebuilt['pronto_wlan.ko'] = work / 'wlan/wlan.ko'
mapping = []
for target in sorted(old_modules.rglob('*.ko')):
    source = rebuilt.get(target.name)
    assert source and source.is_file(), ('No rebuilt module', target.name)
    dest = modules / target.relative_to(old_modules)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    subprocess.run(['/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-strip',
                    '--strip-debug', str(dest)], check=True)
    mapping.append({'target': str(target.relative_to(old_modules)), 'source': str(source),
                    'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
subprocess.run(['python3', str(workspace / 'device-inspection/audit-android10-kernel-modules.py'),
                '--base', str(modules), '--build-dir', str(build),
                '--report', str(candidate / 'module-audit.json')], check=True)
subprocess.run(['python3', str(workspace / 'device-inspection/audit-android10-kernel-modules.py'),
                '--base', str(old_modules), '--build-dir', str(build),
                '--report', str(candidate / 'existing-module-audit.json')], check=True)
rebuilt_audit = json.loads((candidate / 'module-audit.json').read_text())
existing_audit = json.loads((candidate / 'existing-module-audit.json').read_text())
assert len(rebuilt_audit['modules']) == len(existing_audit['modules']) == 15
existing_vermagic = {r['vermagic'] for r in existing_audit['modules']}
assert {r['vermagic'] for r in rebuilt_audit['modules']} == existing_vermagic, 'Module vermagic changed'
config = subprocess.check_output([str(kernel / 'scripts/extract-ikconfig'),
                                   str(build / 'arch/arm/boot/zImage')], text=True)
previous_config = (root / 'backports-candidate/kernel.config').read_text()
def settings(text):
    result = {}
    for line in text.splitlines():
        if line.startswith('CONFIG_'):
            key, value = line.split('=', 1)
            result[key] = value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            result[line[2:-11]] = 'n'
    return result
old_settings, new_settings = settings(previous_config), settings(config)
config_changes = {key: {'before': old_settings.get(key), 'after': new_settings.get(key)}
                  for key in old_settings.keys() | new_settings.keys()
                  if old_settings.get(key) != new_settings.get(key)}
assert set(config_changes) == {'CONFIG_WQ_POWER_EFFICIENT_DEFAULT',
                              'CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE',
                              'CONFIG_CPU_FREQ_DEFAULT_GOV_INTERACTIVE',
                              'CONFIG_DEBUG_GPIO'}, config_changes
required = ['CONFIG_ZRAM=y', 'CONFIG_ZSMALLOC=y', 'CONFIG_ZRAM_LZ4_COMPRESS=y',
            'CONFIG_LZ4_COMPRESS=y', 'CONFIG_LZ4_DECOMPRESS=y', 'CONFIG_MEMCG=y',
            'CONFIG_MEMCG_SWAP=y', 'CONFIG_SECCOMP_FILTER=y', 'CONFIG_ANDROID_BINDER_IPC_32BIT=y',
            'CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"',
            'CONFIG_WQ_POWER_EFFICIENT_DEFAULT=y', 'CONFIG_CPU_FREQ_DEFAULT_GOV_INTERACTIVE=y']
for option in required:
    assert option in config.splitlines(), option
shutil.copyfile(build / 'arch/arm/boot/zImage', candidate / 'zImage')
(candidate / 'kernel.config').write_text(config)
cross = '/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-'
symbols = subprocess.check_output([cross + 'nm', str(build / 'vmlinux')], text=True)
for symbol in ['sys_getrandom', 'lz4_compress', 'lz4_decompress_unknownoutputsize',
               'zcomp_create', 'zram_make_request', 'meminfo_proc_show', 'zs_compact',
               'system_power_efficient_wq', 'cpufreq_gov_interactive']:
    assert any(line.endswith(' ' + symbol) for line in symbols.splitlines()), symbol
subprocess.run(['git', '-C', str(kernel), 'diff', '--check'], check=True)
baseline = json.loads((work / 'baseline-manifest.json').read_text())
original = Path(baseline['source'])
changed_original = [name for name, digest in baseline['files'].items()
                    if not (original / name).is_file() or
                    hashlib.sha256((original / name).read_bytes()).hexdigest() != digest]
assert not changed_original, changed_original
# Include added source files in the patch without committing or changing the
# independent baseline commit. Original project Git state is never modified.
subprocess.run(['git', '-C', str(kernel), 'add', '-N', '.'], check=True)
patch = subprocess.check_output(['git', '-C', str(kernel), 'diff', '--binary'])
(candidate / 'kernel-backports.patch').write_bytes(patch)
interface = json.loads((root / 'interface-test.json').read_text())
codec = json.loads((root / 'arm-lz4-test.json').read_text())
context_test = json.loads((root / 'zram-context-test.json').read_text())
allocator_test = json.loads((root / 'zsmalloc-compaction-test.json').read_text())
policy_test = json.loads((root / 'performance-policy-test.json').read_text())
assert allocator_test['exit_code'] == 0 and allocator_test['allocations'] == 5000
allocator_source = (kernel / 'drivers/staging/zsmalloc/zsmalloc-main.c').read_text()
allocator_source = re.sub(r'^#include .+$', '', allocator_source, flags=re.M)
assert hashlib.sha256(allocator_source.encode()).hexdigest() == allocator_test['allocator_source_sha256']
assert policy_test['fixture_cases'] == 6 and policy_test['content_idempotent']
assert codec['exit_code'] == 0 and interface['MemAvailable_ARM32_cases'] == 10006
assert context_test['free_outside_spinlock_asserted'] and context_test['allocator_mapping_released_before_stream_release']
log = (root / 'logs/performance-build.log').read_text()
assert 'PERFORMANCE KERNEL AND MODULE BUILDS COMPLETE; NO DEVICE ACCESS.' in log
report = {'kernel_sha256': hashlib.sha256((candidate / 'zImage').read_bytes()).hexdigest(),
          'kernel_bytes': (candidate / 'zImage').stat().st_size,
          'compiler': subprocess.check_output([cross + 'gcc', '--version'], text=True).splitlines()[0],
          'modules': mapping, 'embedded_required_config_verified': required,
          'original_source_files_unchanged': len(baseline['files']),
          'build_complete': True, 'codec_test': codec, 'interface_test': interface,
          'config_changes_from_previous_candidate': config_changes,
          'zram_context_test': context_test,
          'allocator_test': allocator_test, 'performance_policy_test': policy_test,
          'hardware_tested': False, 'physical_phone_access_forbidden': True,
          'runtime_limitations': ['Not boot-tested; zram concurrency, memory pressure and boot-time entropy not verified.',
                                 'Existing Wi-Fi, camera, modem and tearing issues are not claimed fixed.']}
(candidate / 'build-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print('Verified kernel', report['kernel_sha256'], 'modules', len(mapping),
      'unchanged original source files', len(baseline['files']))
