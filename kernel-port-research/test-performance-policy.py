"""Run the delivered one-shot shell policy solely against temporary host fixtures."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parent
policy = root / 'performance-policy.sh'
subprocess.run(['sh', '-n', str(policy)], check=True)
subprocess.run(['sh', '-n', str(root / 'performance-post-boot.sh')], check=True)
cases = [
    ('normal', '300000', '1094400', 'interactive ondemand performance', '512', '300000', 'interactive', '85', '128'),
    ('unsupported-governor', '300000', '1094400', 'ondemand performance', '64', '300000', 'ondemand', '1 800000:85', '64'),
    ('bad-minimum', 'bad', '1094400', 'interactive', '128', '800000', 'interactive', '85', '128'),
    ('minimum-over-cap', '1400000', '1094400', 'interactive', 'bad', '800000', 'interactive', '85', 'bad'),
    ('zero-minimum', '0', '1094400', 'interactive', '512', '800000', 'interactive', '85', '128'),
]
for name, minimum, maximum, governors, readahead, expected_min, expected_gov, expected_loads, expected_ra in cases:
    with tempfile.TemporaryDirectory(prefix='kyf37-policy-') as tmp:
        base = Path(tmp)
        cpu = base / 'devices/system/cpu/cpu0/cpufreq'
        interactive = base / 'devices/system/cpu/cpufreq/interactive'
        core = base / 'devices/system/cpu/cpu0/core_ctl'
        mmc = base / 'block/mmcblk0/queue'
        for p in (cpu, interactive, core, mmc):
            p.mkdir(parents=True)
        inputs = {cpu / 'cpuinfo_min_freq': minimum, cpu / 'scaling_max_freq': maximum,
                  cpu / 'scaling_available_governors': governors,
                  cpu / 'scaling_governor': 'ondemand', cpu / 'scaling_min_freq': '800000',
                  interactive / 'target_loads': '1 800000:85', core / 'min_cpus': '2',
                  mmc / 'read_ahead_kb': readahead}
        for p, text in inputs.items():
            p.write_text(text + '\n')
        env = dict(os.environ, KYF37_SYSFS_ROOT=str(base))
        subprocess.run(['sh', str(policy)], env=env, check=True, timeout=10)
        assert (cpu / 'scaling_min_freq').read_text().strip() == expected_min, name
        assert (cpu / 'scaling_governor').read_text().strip() == expected_gov, name
        assert (interactive / 'target_loads').read_text().strip() == expected_loads, name
        assert (mmc / 'read_ahead_kb').read_text().strip() == expected_ra, name
        assert (core / 'min_cpus').read_text().strip() == '1'
        assert (cpu / 'scaling_max_freq').read_text().strip() == maximum
        before = {p: p.read_bytes() for p in inputs}
        subprocess.run(['sh', str(policy)], env=env, check=True, timeout=10)
        assert before == {p: p.read_bytes() for p in inputs}, name
        if name == 'normal':
            # Run the delivered wrapper with host-only paths. The fake vendor
            # setup restores the old floor, proving that tuning follows it.
            vendor = base / 'vendor-post-boot.sh'
            vendor.write_text('printf "800000\\n" > "' + str(cpu / 'scaling_min_freq') + '"\nexit 17\n')
            wrapper = (root / 'performance-post-boot.sh').read_text()
            wrapper = wrapper.replace('/system/bin/sh', '/bin/sh')
            wrapper = wrapper.replace('/system/etc/init.qcom.post_boot.sh', str(vendor))
            wrapper = wrapper.replace('/kyf37-performance-policy.sh', str(policy))
            stub = base / 'wrapper.sh'
            stub.write_text(wrapper)
            result = subprocess.run(['sh', str(stub)], env=env, timeout=10)
            assert result.returncode == 17
            assert (cpu / 'scaling_min_freq').read_text().strip() == '300000'
with tempfile.TemporaryDirectory(prefix='kyf37-policy-missing-') as tmp:
    subprocess.run(['sh', str(policy)], env=dict(os.environ, KYF37_SYSFS_ROOT=tmp), check=True, timeout=10)
    assert not list(Path(tmp).iterdir())
report = {'fixture_cases': len(cases) + 1, 'content_idempotent': True,
          'wrapper_runs_after_vendor_setup_and_preserves_exit_status': True,
          'maximum_frequency_preserved': True, 'physical_phone_access': False,
          'limitation': 'Host shell/regular-file fixtures; no sysfs, SELinux or hardware runtime validation.'}
(root / 'performance-policy-test.json').write_text(json.dumps(report, indent=2) + '\n')
print(report)
