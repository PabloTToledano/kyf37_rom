"""Keep all stock QCDT entries for observed SoC 245 / hardware platform MTP."""
from pathlib import Path
import hashlib,json,struct
p=Path(__file__).resolve().parent
raw=(p/'recovery-stock/dt').read_bytes()
magic,version,count=struct.unpack_from('<3I',raw)
assert magic==0x54444351 and version==3
entries=[list(struct.unpack_from('<10I',raw,12+i*40)) for i in range(count)]
keep=[e for e in entries if e[0]==245 and (e[1]&255)==8]
assert len(keep)==6 and any(e[2]==2 for e in keep)
align=lambda n:(n+2047)//2048*2048
out=bytearray(align(12+len(keep)*40))
struct.pack_into('<3I',out,0,magic,version,len(keep))
blobs={};report=[]
for i,e in enumerate(keep):
    old=e[8];size=e[9]
    blob=raw[old:old+size]
    assert len(blob)==size and blob[:4]==b'\xd0\x0d\xfe\xed'
    k=(old,size)
    if k not in blobs:
        blobs[k]=len(out)
        out.extend(blob)
        out.extend(bytes(align(len(out))-len(out)))
    e[8]=blobs[k]
    struct.pack_into('<10I',out,12+i*40,*e)
    assert out[e[8]:e[8]+size]==blob
    report.append({'fields':e,'original_offset':old,'blob_sha256':hashlib.sha256(blob).hexdigest()})
(p/'kyf37-mtp-dt.img').write_bytes(out)
(p/'kyf37-mtp-dt-validation.json').write_text(json.dumps({'original_bytes':len(raw),'output_bytes':len(out),'original_count':count,'kept_count':len(keep),'runtime_soc_id':245,'runtime_hw_platform':'MTP','runtime_subtype':2,'source_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'entries':report},indent=2))
print('DT bytes:',len(raw),'->',len(out),'entries:',count,'->',len(keep))
