"""Offline ROM boot signing with the already enrolled KYF37 owner key."""
from pathlib import Path
import argparse,struct,json,hashlib
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import padding
root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('source',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
assert args.source.resolve()!=args.output.resolve()
assert not args.output.exists(),'Choose a new output file; never overwrite signed artifacts.'
def read(data,pos=0):
 start=pos;tag=data[pos];pos+=1;n=data[pos];pos+=1
 if n&128:
  count=n&127;assert 0<count<=4
  n=int.from_bytes(data[pos:pos+count],'big');pos+=count
 end=pos+n;assert end<=len(data)
 return tag,data[pos:end],data[start:end],end
def children(data):
 result=[];pos=0
 while pos<len(data):
  item=read(data,pos);result.append(item);pos=item[3]
 return result
def tlv(tag,data):
 n=len(data);count=max(1,(n.bit_length()+7)//8)
 length=bytes([n]) if n<128 else bytes([128+count])+n.to_bytes(count,'big')
 return bytes([tag])+length+data
def seq(*items):return tlv(48,b''.join(items))
def body(data):
 assert data[:8]==b'ANDROID!'
 fields=struct.unpack_from('<10I',data,8);page=fields[7]
 assert page in (2048,4096,8192,16384)
 end=page+sum((n+page-1)//page*page for n in (fields[0],fields[2],fields[4],fields[8]))
 assert end<=len(data)
 return end
owner=root/'kyf37-twrp-device'
private=serialization.load_pem_private_key((owner/'owner-signing-key.pem').read_bytes(),None)
public=private.public_key()
public_der=public.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.PKCS1)
assert public_der==(owner/'owner-public-key.der').read_bytes()
ks=children(read((owner/'owner-keystore.img').read_bytes())[1])
assert children(children(ks[1][1])[0][1])[1][2]==public_der
template=(root/'phone-backup/kyf37-root-backup/boot.img').read_bytes()
fields=children(read(template,body(template))[1]);assert len(fields)==5
data=args.source.read_bytes();end=body(data)
size=end.to_bytes(max(1,(end.bit_length()+7)//8),'big')
if size[0]&128:size=b'\0'+size
attributes=seq(tlv(19,b'/boot'),tlv(2,size))
signature=private.sign(data[:end]+attributes,padding.PKCS1v15(),hashes.SHA256())
envelope=seq(fields[0][2],fields[1][2],fields[2][2],attributes,tlv(4,signature))
image=data[:end]+envelope
assert len(image)<=16777216
image+=bytes(16777216-len(image))
public.verify(signature,image[:end]+attributes,padding.PKCS1v15(),hashes.SHA256())
assert image[:end]==data[:end]
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_bytes(image)
report={'source':str(args.source.resolve()),'output':str(args.output.resolve()),
 'target':'/boot','body_bytes':end,'partition_bytes':len(image),
 'body_preserved':True,'signature_verified':True,
 'sha256':hashlib.sha256(image).hexdigest(),
 'scope':'Offline signature verification; actual enrolled phone keystore and bootability require separate checks.'}
args.output.with_suffix('.signing.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
