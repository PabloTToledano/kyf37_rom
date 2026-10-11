"""Create unsigned, uninstalled boot candidates using the v13 release ramdisk.

No ADB, partition access, signing-key access, or existing-tree writes.
"""
from pathlib import Path
import gzip
import hashlib
import json
import re
import struct
import subprocess

root = Path(__file__).resolve().parent
workspace = root.parent
candidate = root / 'backports-candidate'
base = workspace / 'kyf37-rom/android10-go-candidate-20261007-v13/boot-android10-unsigned.img'
base_report = json.loads((base.parent / 'android10-image-validation.json').read_text())
raw = base.read_bytes()
assert hashlib.sha256(raw).hexdigest() == base_report['boot']['sha256']
assert raw[:8] == b'ANDROID!'
verification = json.loads((candidate / 'build-verification.json').read_text())
kernel = (candidate / 'zImage').read_bytes()
assert hashlib.sha256(kernel).hexdigest() == verification['kernel_sha256']
audit = json.loads((candidate / 'module-audit.json').read_text())
assert {m['vermagic'] for m in audit['modules']} == {
    '3.10.49 SMP preempt mod_unload modversions ARMv7 p2v8 '}
fields = struct.unpack_from('<10I', raw, 8)
page = fields[7]
assert page == 2048 and fields[8] > 2
offset, blobs = page, []
for size in (fields[0], fields[2], fields[4], fields[8]):
    blob = raw[offset:offset + size]
    assert len(blob) == size
    blobs.append(blob)
    offset += (size + page - 1) // page * page
assert offset == len(raw)

def parse_cpio(archive):
    entries, pos = {}, 0
    while pos + 110 <= len(archive):
        assert archive[pos:pos + 6] == b'070701'
        header = [int(archive[pos + 6 + i * 8:pos + 14 + i * 8], 16) for i in range(13)]
        name = archive[pos + 110:pos + 110 + header[11] - 1].decode()
        start = (pos + 110 + header[11] + 3) & ~3
        data = archive[start:start + header[6]]
        assert len(data) == header[6]
        if name == 'TRAILER!!!':
            return entries
        assert name not in entries
        entries[name] = (header, data)
        pos = (start + header[6] + 3) & ~3
    raise AssertionError('Missing CPIO trailer')

def pack_cpio(entries):
    out = bytearray()
    for name, (original, data) in list(entries.items()) + [('TRAILER!!!', ([0] * 13, b''))]:
        h = list(original)
        h[6], h[11], h[12] = len(data), len(name.encode()) + 1, 0
        out.extend(b'070701' + ''.join(f'{v:08x}' for v in h).encode())
        out.extend(name.encode() + b'\0')
        out.extend(bytes((-len(out)) % 4))
        out.extend(data)
        out.extend(bytes((-len(out)) % 4))
    out.extend(bytes((-len(out)) % 512))
    return bytes(out)

entries = parse_cpio(gzip.decompress(blobs[1]))
assert 'kyf37-init-debug' not in entries
for name, (_, content) in entries.items():
    if name.endswith(('.rc', '.sh')):
        assert b'service kyf37-trial-return' not in content, name
        assert b'start kyf37-trial-return' not in content, name
        assert b'boot-recovery' not in content, name

def make_boot(name, ramdisk):
    selected = [kernel, ramdisk, blobs[2], blobs[3]]
    header = bytearray(raw[:page])
    struct.pack_into('<I', header, 8, len(kernel))
    struct.pack_into('<I', header, 16, len(ramdisk))
    digest = hashlib.sha1()
    for blob in selected:
        digest.update(blob)
        digest.update(struct.pack('<I', len(blob)))
    header[576:608] = digest.digest() + bytes(12)
    result = bytes(header) + b''.join(blob + bytes((-len(blob)) % page) for blob in selected)
    assert len(result) <= 16777216
    output = candidate / name
    output.write_bytes(result)
    subprocess.run(['python3', str(workspace / 'device-inspection/verify-rom-boot.py'), str(output),
                    '--expected-kernel', str(candidate / 'zImage'), '--kernel-policy-max', '30',
                    '--require-legacy-first-stage', '--report', str(output.with_suffix('.validation.json'))],
                   check=True)
    return {'path': name, 'sha256': hashlib.sha256(result).hexdigest(), 'bytes': len(result),
            'owner_signed': False, 'installed': False, 'hardware_tested': False}

outputs = [make_boot('boot-kernel-backports-unsigned.img', blobs[1])]
tuned = {name: (list(header), content) for name, (header, content) in entries.items()}
modified = []
for name in ('init.target.rc', 'init.qcom.rc', 'fstab.qcom'):
    header, data = tuned[name]
    text = data.decode()
    if name == 'init.target.rc':
        # This supersedes the legacy property-driven, 512MB zram action.
        text, count = re.subn(r'^on property:ro\.config\.zram=true\n(?:[ \t]+[^\n]*\n)*',
                             '# Zram is configured by init.kyf37.memory.rc.\n', text, flags=re.M)
        assert count == 1
    elif name == 'init.qcom.rc':
        text = re.sub(r'^[ \t]+start config-zram\n', '', text, flags=re.M)
    else:
        text, count = re.subn(r'^/dev/block/zram0\s+[^\n]*\n', '', text, flags=re.M)
        assert count == 1
    tuned[name] = (header, text.encode())
    modified.append(name)
header, data = tuned['init.rc']
tuned['init.rc'] = (header, data.rstrip() + b'\n\nimport /init.kyf37.memory.rc\n')
modified.append('init.rc')
memory_rc = '''# Experimental memory policy for KYF37, host-validated only.
on post-fs-data
    write /sys/block/zram0/comp_algorithm lz4
    write /sys/block/zram0/max_comp_streams 4
    write /sys/block/zram0/mem_limit 134217728
    swapon_all /fstab.kyf37.zram
    write /proc/sys/vm/page-cluster 0
    write /proc/sys/vm/swappiness 100
'''
zram_fstab = '/dev/block/zram0 none swap defaults zramsize=268435456,swapprio=100\n'
for name, data in [('init.kyf37.memory.rc', memory_rc), ('fstab.kyf37.zram', zram_fstab)]:
    h = [0] * 13
    h[0], h[1], h[4] = 100000 + len(tuned), 0o100644, 1
    tuned[name] = (h, data.encode())
    (candidate / name).write_text(data)
    modified.append(name)
init_review = candidate / 'ramdisk-init-review'
init_review.mkdir(exist_ok=True)
host_init_verifier = '/home/pablo/kyf37-android10/out/host/linux-x86/bin/host_init_verifier'
for name in ('init.rc', 'init.target.rc', 'init.qcom.rc', 'init.kyf37.memory.rc'):
    (init_review / name).write_bytes(tuned[name][1])
    subprocess.run([host_init_verifier, str(init_review / name)], check=True)
new_archive = pack_cpio(tuned)
reparsed = parse_cpio(new_archive)
assert reparsed.keys() == tuned.keys()
assert all(reparsed[name][1] == content and reparsed[name][0][1:5] == header[1:5]
           for name, (header, content) in tuned.items())
outputs.append(make_boot('boot-memory-tuned-unsigned.img', gzip.compress(new_archive, compresslevel=9, mtime=0)))
report = {'base_release': str(base), 'base_sha256': base_report['boot']['sha256'],
          'kernel_sha256': verification['kernel_sha256'], 'outputs': outputs,
          'stock_OEM_DT_and_boot_geometry_preserved': True,
          'kernel_only_ramdisk_byte_identical_to_v13': True,
          'Android_10_host_init_verifier_passed': True,
          'tuned_ramdisk_changed_entries': modified,
          'tuning': {'logical_zram_bytes': 268435456, 'physical_zram_limit_bytes': 134217728,
                     'compressor': 'lz4', 'max_streams': 4, 'swap_readahead_page_cluster': 0,
                     'swappiness': 100},
          'note': 'Unsigned experimental artifacts; no installation, reboot or phone testing performed.'}
(candidate / 'boot-packaging.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
