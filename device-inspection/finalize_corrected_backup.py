"""Validate the completed corrected image, preserving native GPT discrepancies."""
import hashlib,json,struct,zlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent
folder=root/'phone-backup'
source=folder/'mmcblk0-corrected.img.partial'
target=folder/'mmcblk0-corrected.img'
mapping=json.loads((folder/'partition-map.json').read_text())
assert not target.exists()
expected=mapping['expected_disk_bytes']
assert source.stat().st_size==expected
digest=hashlib.sha256()
with source.open('rb') as f:
    head=f.read(34*512)
    assert head==(folder/'gpt-head-device.bin').read_bytes()
    f.seek(expected-33*512)
    tail=f.read(33*512)
    assert tail==(folder/'gpt-tail-device.bin').read_bytes()
    for region,header_index,table in [(head,512,head[1024:]),(tail,32*512,tail)]:
        sector=region[header_index:header_index+512]
        assert sector[:8]==b'EFI PART'
        size,crc=struct.unpack_from('<II',sector,12)
        assert 92<=size<=512
        h=bytearray(sector[:size]);h[16:20]=bytes(4)
        assert zlib.crc32(h)&0xffffffff==crc
        _,count,entry_size,table_crc=struct.unpack_from('<QIII',sector,72)
        assert zlib.crc32(table[:count*entry_size])&0xffffffff==table_crc
    stock={}
    for name in ('boot','recovery','aboot','devinfo'):
        p=next(p for p in mapping['partitions'] if p['name']==name)
        f.seek(p['offset_bytes'])
        stock[name]=f.read(p['bytes'])==(folder/'kyf37-root-backup'/f'{name}.img').read_bytes()
    assert all(stock.values()),stock
    p=next(p for p in mapping['partitions'] if p['name']=='system')
    f.seek(p['offset_bytes']);system=hashlib.sha256();remaining=p['bytes']
    while remaining:
        data=f.read(min(16*1024*1024,remaining));assert data
        system.update(data);remaining-=len(data)
    system_evidence=json.loads((folder/'system-corrected-stream-hash.json').read_text())
    assert system.hexdigest()==system_evidence['on_device_sha256'] and system_evidence['on_device_hash_matches']
    f.seek(0)
    while data:=f.read(16*1024*1024):digest.update(data)
report={'path':str(target),'bytes':expected,'sha256':digest.hexdigest(),
        'both_gpt_copies_match_fresh_phone_reads':True,'both_gpt_crc_valid':True,
        'native_gpt_discrepancy':'Type GUIDs for partitions 2–9 differ between primary and backup on the phone; preserved without modification',
        'stock_partitions_match':stock,'full_system_matches_phone_sha256':system.hexdigest(),
        'correction':json.loads((folder/'stream-insertion-evidence.json').read_text()),
        'scope':'complete eMMC user area; excludes hardware RPMB',
        'consistency':'Live mounted filesystems; not guaranteed offline-consistent',
        'modem_state':'Image captured before Spanish LTE preference change'}
source.rename(target)
(folder/'mmcblk0-corrected-manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
