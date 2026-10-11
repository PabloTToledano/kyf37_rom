"""Preserve source and remove one proven diagnostic insertion into a new image."""
import hashlib, json, struct, zlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent
folder=root/'phone-backup'
evidence=json.loads((folder/'stream-insertion-evidence.json').read_text())
mapping=json.loads((folder/'partition-map.json').read_text())
source=folder/'mmcblk0-live.img.partial'
target=folder/'mmcblk0-corrected.img'
temporary=folder/'mmcblk0-corrected.img.partial'
expected=mapping['expected_disk_bytes']
extra=bytes.fromhex(evidence['extra_bytes_hex'])
offset=evidence['insertion_offset']
assert evidence['local_window_matches_after_removing47']
assert source.stat().st_size==expected+len(extra), 'Source not complete at expected contaminated size'
assert not target.exists() and not temporary.exists(), 'Refusing to overwrite correction output'
digest=hashlib.sha256()
with source.open('rb') as src, temporary.open('xb') as dst:
    src.seek(offset)
    assert src.read(len(extra))==extra, 'Insertion differs from evidence'
    src.seek(0)
    for length in (offset,expected-offset):
        remaining=length
        while remaining:
            data=src.read(min(16*1024*1024,remaining))
            assert data
            dst.write(data)
            digest.update(data)
            remaining-=len(data)
        if src.tell()==offset:
            assert src.read(len(extra))==extra
assert temporary.stat().st_size==expected
def check_gpt(f,lba):
    f.seek(lba*512)
    sector=f.read(512)
    assert sector[:8]==b'EFI PART'
    size,crc=struct.unpack_from('<II',sector,12)
    assert 92<=size<=512
    header=bytearray(sector[:size]);header[16:20]=bytes(4)
    assert zlib.crc32(header)&0xffffffff==crc
    table_lba,count,entry_size,table_crc=struct.unpack_from('<QIII',sector,72)
    assert count<=4096 and 128<=entry_size<=4096
    f.seek(table_lba*512)
    table=f.read(count*entry_size)
    assert len(table)==count*entry_size and zlib.crc32(table)&0xffffffff==table_crc
    return sector,table
with temporary.open('rb') as f:
    primary,pt=check_gpt(f,1)
    secondary,st=check_gpt(f,expected//512-1)
    assert pt==st
    assert struct.unpack_from('<Q',primary,24)[0]==1
    assert struct.unpack_from('<Q',secondary,32)[0]==1
    matches={}
    for name in ('boot','recovery','aboot','devinfo'):
        entry=next(p for p in mapping['partitions'] if p['name']==name)
        f.seek(entry['offset_bytes'])
        matches[name]=f.read(entry['bytes'])==(folder/'kyf37-root-backup'/f'{name}.img').read_bytes()
    assert all(matches.values()),matches
temporary.rename(target)
report={'source':str(source),'path':str(target),'bytes':expected,'sha256':digest.hexdigest(),
        'removed_offset':offset,'removed_hex':extra.hex(),'both_gpt_crcs_valid':True,
        'gpt_tables_match':True,'stock_partition_matches':matches,
        'validation_remaining':'Compare full immutable system hash to phone',
        'consistency':'Live mounted filesystems; not guaranteed offline-consistent',
        'scope':'eMMC user area; excludes hardware RPMB'}
(folder/'mmcblk0-corrected-manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
