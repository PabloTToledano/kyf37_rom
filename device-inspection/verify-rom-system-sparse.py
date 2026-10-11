"""Validate the complete sparse container against the recorded system geometry."""
from pathlib import Path
import argparse,struct,json,hashlib
parser=argparse.ArgumentParser()
parser.add_argument('image',type=Path)
parser.add_argument('--report',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
partition=json.loads((root/'phone-backup/partition-map.json').read_text())
system=next(p for p in partition['partitions'] if p['name']=='system')
sha=hashlib.sha256()
with args.image.open('rb') as stream:
    head=stream.read(28)
    magic,major,minor,file_header,chunk_header,block_size,total_blocks,chunks,checksum=struct.unpack('<I4H4I',head)
    assert magic==0xed26ff3a and major==1
    assert file_header>=28 and chunk_header>=12 and block_size==4096
    assert total_blocks*block_size==system['bytes']
    stream.seek(file_header)
    blocks=0;types={}
    for i in range(chunks):
        raw=stream.read(chunk_header);assert len(raw)==chunk_header
        kind,reserved,count,size=struct.unpack_from('<2H2I',raw)
        assert size>=chunk_header
        payload=size-chunk_header
        if kind==0xcac1:assert payload==count*block_size
        elif kind==0xcac2:assert payload==4
        elif kind==0xcac3:assert payload==0
        elif kind==0xcac4:assert payload==4 and count==0
        else:raise AssertionError(('Unknown chunk',hex(kind)))
        stream.seek(payload,1)
        assert stream.tell()<=args.image.stat().st_size
        blocks+=count
        types[hex(kind)]=types.get(hex(kind),0)+1
    assert blocks==total_blocks
    assert stream.tell()==args.image.stat().st_size,'Trailing or truncated sparse data'
with args.image.open('rb') as stream:
    for chunk in iter(lambda:stream.read(4*1024*1024),b''):sha.update(chunk)
report={'image':str(args.image.resolve()),'sha256':sha.hexdigest(),
        'sparse_bytes':args.image.stat().st_size,'expanded_bytes':blocks*block_size,
        'partition_bytes':system['bytes'],'chunks':chunks,'chunk_types':types,
        'scope':'Complete sparse-container structure and exact partition geometry; filesystem contents and runtime unverified.'}
(args.report or root/'kyf37-rom/system-sparse-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
