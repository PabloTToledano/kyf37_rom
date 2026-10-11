"""Read-only unpack of the backed-up legacy Android recovery image."""
import gzip, hashlib, json, struct
from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = root / 'phone-backup/kyf37-root-backup/recovery.img'
out = root / 'device-inspection/recovery-stock'
data = source.read_bytes()
assert data[:8] == b'ANDROID!'
fields = struct.unpack_from('<10I', data, 8)
ks, ka, rs, ra, ss, sa, tags, page, dt, unused = fields
assert page in (2048, 4096, 8192, 16384)
align = lambda n: (n + page - 1) // page * page
offset = page
out.mkdir(exist_ok=True)
for name, size in [('kernel', ks), ('ramdisk.gz', rs), ('second', ss), ('dt', dt)]:
    blob = data[offset:offset + size]
    assert len(blob) == size
    if size:
        (out / name).write_bytes(blob)
    offset += align(size)
cpio = gzip.decompress((out / 'ramdisk.gz').read_bytes())
(out / 'ramdisk.cpio').write_bytes(cpio)
entries = []
pos = 0
while pos + 110 <= len(cpio):
    assert cpio[pos:pos+6] in (b'070701', b'070702')
    h = [int(cpio[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
    size, namesize = h[6], h[11]
    name = cpio[pos+110:pos+110+namesize-1].decode()
    start = (pos+110+namesize+3) & ~3
    payload = cpio[start:start+size]
    entries.append({'name': name, 'bytes': size, 'mode': oct(h[1])})
    if name == 'TRAILER!!!':
        break
    if name.endswith('fstab') or 'fstab.' in name or name.endswith('.rc'):
        # Save flat names; never trust archive paths as filesystem destinations.
        (out / name.replace('/', '__')).write_bytes(payload)
    pos = (start+size+3) & ~3
report = {'source_sha256': hashlib.sha256(data).hexdigest(), 'partition_bytes':len(data),
          'kernel_bytes':ks, 'ramdisk_bytes':rs, 'dt_bytes':dt, 'page_size':page,
          'kernel_address':hex(ka), 'ramdisk_address':hex(ra), 'tags_address':hex(tags),
          'cmdline':data[64:576].split(b'\0')[0].decode(errors='replace'), 'entries':entries}
(out / 'inspection.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if k != 'entries'}, indent=2))
