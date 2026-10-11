from pathlib import Path
import struct,hashlib,json
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
source=root/'kyf37-rom/android10-go-candidate-20261007-v8/boot-android10-unsigned.img'
out=root/'kyf37-rom/boot-v8-v9-kernel-test-unsigned.img'
assert not out.exists()
data=source.read_bytes();assert hashlib.sha256(data).hexdigest()=='d88a31561b7ff9e11261960ec6ed09412ac9d170e93ae988ac4f882e8f139b95'
fields=struct.unpack_from('<10I',data,8);page=fields[7];assert page==2048
pos=page;blobs=[]
for size in (fields[0],fields[2],fields[4],fields[8]):
 blobs.append(data[pos:pos+size]);pos+=(size+page-1)//page*page
assert pos==len(data)
old_kernel_sha=hashlib.sha256(blobs[0]).hexdigest()
blobs[0]=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/kernel').read_bytes()
assert hashlib.sha256(blobs[0]).hexdigest()=='a7de7aad86bd0b111ec937aeee334a9460792e4367d24d4775b29ff70f8aa521'
header=bytearray(data[:page]);struct.pack_into('<I',header,8,len(blobs[0]))
h=hashlib.sha1()
for blob in blobs:h.update(blob);h.update(struct.pack('<I',len(blob)))
header[576:608]=h.digest()+bytes(12)
result=bytes(header)+b''.join(b+bytes((-len(b))%page) for b in blobs)
out.write_bytes(result)
report={'source':str(source),'output':str(out),'bytes':len(result),'sha256':hashlib.sha256(result).hexdigest(),'old_kernel_sha256':old_kernel_sha,'kernel_sha256':hashlib.sha256(blobs[0]).hexdigest(),'unchanged_ramdisk_dt_and_arguments':True}
(root/'device-inspection/v9-kernel-only-repack.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
