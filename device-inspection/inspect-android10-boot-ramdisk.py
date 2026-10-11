from pathlib import Path
import struct,gzip
data=Path('/home/pablo/kyf37-android10/out/target/product/kyf37/boot.img').read_bytes()
fields=struct.unpack_from('<10I',data,8)
page=fields[7]; offset=page+(fields[0]+page-1)//page*page
archive=gzip.decompress(data[offset:offset+fields[2]])
pos=0
while pos+110<=len(archive):
    assert archive[pos:pos+6] in (b'070701',b'070702')
    header=[int(archive[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
    size,namesize=header[6],header[11]
    name=archive[pos+110:pos+110+namesize-1].decode()
    start=(pos+110+namesize+3)&~3
    print(name,size,oct(header[1]))
    if name.endswith(('init.rc','fstab.qcom','init.environ.rc')):
        print(archive[start:start+size].decode(errors='replace')[:2500])
    if name=='TRAILER!!!':break
    pos=(start+size+3)&~3
