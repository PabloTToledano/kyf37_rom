"""Check repeatability, patch applicability and all delivered artifact hashes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
kernel = work / 'kernel'
candidate = root / 'backports-candidate'
before = subprocess.check_output(['git', '-C', str(kernel), 'diff', '--binary'])
subprocess.run(['python3', str(root / 'backport-working-kernel.py')], check=True)
after = subprocess.check_output(['git', '-C', str(kernel), 'diff', '--binary'])
assert before == after, 'Backport script was not content-idempotent'
assert after == (candidate / 'kernel-backports.patch').read_bytes(), 'Patch differs from final source'
env = dict(os.environ, GIT_INDEX_FILE=str(work / 'patch-audit.index'))
subprocess.run(['git', '-C', str(kernel), 'read-tree', 'HEAD'], env=env, check=True)
subprocess.run(['git', '-C', str(kernel), 'apply', '--cached', '--check',
                str(candidate / 'kernel-backports.patch')], env=env, check=True)
build = json.loads((candidate / 'build-verification.json').read_text())
boot = json.loads((candidate / 'boot-packaging.json').read_text())
assert build['build_complete'] and not build['hardware_tested']
assert build['original_source_files_unchanged'] == 47017
assert boot['kernel_sha256'] == build['kernel_sha256']
assert boot['Android_10_host_init_verifier_passed']
assert len(boot['outputs']) == 2
for output in boot['outputs']:
    data = (candidate / output['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == output['sha256']
    assert len(data) == output['bytes'] <= 16777216
    assert not any(output[k] for k in ('owner_signed', 'installed', 'hardware_tested'))
for name in ('module-audit.json', 'existing-module-audit.json'):
    audit = json.loads((candidate / name).read_text())
    assert len(audit['modules']) == 15
    for module in audit['modules']:
        assert module['vermagic'] == '3.10.49 SMP preempt mod_unload modversions ARMv7 p2v8 '
        assert not any(module[k] for k in ('missing_exports', 'crc_mismatches', 'unsupported_loaded_relocations'))
        assert module['has_versions']
result = {'source_script_content_idempotent': True, 'patch_applies_to_working_snapshot': True,
          'final_kernel_and_boot_hashes_consistent': True, 'rebuilt_modules_verified': 15,
          'existing_modules_verified': 15, 'host_init_verified': True,
          'original_kernel_files_preserved': 47017, 'physical_phone_access': False,
          'hardware_runtime_verified': False}
(candidate / 'final-audit.json').write_text(json.dumps(result, indent=2) + '\n')
files = sorted(p for p in candidate.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(candidate / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() +
    '  ' + str(p.relative_to(candidate)) + '\n' for p in files))
for line in (candidate / 'SHA256SUMS').read_text().splitlines():
    digest, name = line.split('  ', 1)
    assert hashlib.sha256((candidate / name).read_bytes()).hexdigest() == digest
print(json.dumps(result, indent=2))
