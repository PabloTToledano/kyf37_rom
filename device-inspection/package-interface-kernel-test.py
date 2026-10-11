from pathlib import Path
import struct,hashlib,json
r=Path(__file__).resolve().parent.parent
source=r/'kyf37-rom/diagnose-v3/stock-kernel-control-unsigned.img'
out=r/'kyf37-rom/diagnose-v3/interfaces-kernel-test-unsigned.img'
assert not out.exists()
data=source.read_bytes();fields=struct.unpack_from('<10I',data,8);page=fields[7];assert page==2048
pos=page;blobs=[]
for size in (fields[0],fields[2],fields[4],fields[8]):
 blobs.append(data[pos:pos+size]);pos+=(size+page-1)//page*page
blobs[0]=(r/'kyf37-rom/diagnose-v3/kernel-android10-interfaces').read_bytes()
header=bytearray(data[:page]);struct.pack_into('<I',header,8,len(blobs[0]))
sha=hashlib.sha1()
for blob in blobs: sha.update(blob);sha.update(struct.pack('<I',len(blob)))
header[576:608]=sha.digest()+bytes(12)
result=bytes(header)+b''.join(b+bytes((-len(b))%page) for b in blobs)
out.write_bytes(result)
print(json.dumps({'output':str(out),'sha256':hashlib.sha256(result).hexdigest(),'kernel_sha256':hashlib.sha256(blobs[0]).hexdigest(),'bytes':len(result),'only_kernel_changed':True}))
