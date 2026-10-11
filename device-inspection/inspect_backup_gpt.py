"""Validate the primary GPT in a complete or still-growing eMMC backup."""
import json, struct, zlib
from pathlib import Path

root = Path(__file__).resolve().parent.parent
final = root / 'phone-backup/mmcblk0-live.img'
source = final if final.exists() else final.with_suffix('.img.partial')
with source.open('rb') as f:
    f.seek(512)
    sector = f.read(512)
    assert sector[:8] == b'EFI PART'
    size, stored_crc = struct.unpack_from('<II', sector, 12)
    assert 92 <= size <= 512
    header = bytearray(sector[:size])
    header[16:20] = bytes(4)
    assert zlib.crc32(header) & 0xffffffff == stored_crc, 'GPT header CRC mismatch'
    current, backup, first, last = struct.unpack_from('<4Q', sector, 24)
    table_lba, count, entry_size, table_crc = struct.unpack_from('<QIII', sector, 72)
    assert count <= 4096 and 128 <= entry_size <= 4096
    f.seek(table_lba * 512)
    table = f.read(count * entry_size)
    assert len(table) == count * entry_size
    assert zlib.crc32(table) & 0xffffffff == table_crc, 'GPT partition CRC mismatch'
entries = []
for i in range(count):
    entry = table[i*entry_size:(i+1)*entry_size]
    if not any(entry[:16]): continue
    start, end, attributes = struct.unpack_from('<QQQ', entry, 32)
    assert first <= start <= end <= last
    entries.append({'number':i+1, 'name':entry[56:128].decode('utf-16-le').split('\0')[0],
                    'offset_bytes':start*512, 'bytes':(end-start+1)*512,
                    'start_lba':start, 'end_lba':end, 'attributes':hex(attributes)})
for a,b in zip(sorted(entries,key=lambda e:e['start_lba']), sorted(entries,key=lambda e:e['start_lba'])[1:]):
    assert a['end_lba'] < b['start_lba'], 'Overlapping partitions'
report = {'source':str(source), 'primary_header_crc_valid':True, 'partition_table_crc_valid':True,
          'expected_disk_bytes':(backup+1)*512, 'backup_gpt_lba':backup,
          'partitions':entries, 'scope':'Primary GPT only; full image and backup GPT not yet checked'}
(root / 'phone-backup/partition-map.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='partitions'},indent=2))
for entry in entries:
    print(f"{entry['number']:2} {entry['name']:12} {entry['bytes']:12} offset={entry['offset_bytes']}")
