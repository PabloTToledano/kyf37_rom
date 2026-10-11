"""Read OEM identity table candidates from public stock ELF binaries, offline."""
from pathlib import Path
import struct,json
base=Path('/home/pablo/kyf37-rom/stock-system/lib');rows=[]
for name in ['libc.so','libcutils.so']:
 p=base/name;b=p.read_bytes();phoff=struct.unpack_from('<I',b,28)[0];size,count=struct.unpack_from('<HH',b,42)
 segments=[struct.unpack_from('<8I',b,phoff+i*size) for i in range(count)]
 for label in ['root','system','radio','nfc','kmfc']:
  start=0
  while True:
   offset=b.find(label.encode()+b'\0',start)
   if offset<0:break
   start=offset+1
   if offset and b[offset-1]!=0:continue
   addresses=[vaddr+offset-off for typ,off,vaddr,_,filesz,*rest in segments if typ==1 and off<=offset<off+filesz]
   for address in addresses:
    at=0
    while True:
     at=b.find(struct.pack('<I',address),at)
     if at<0:break
     if at%4==0 and at+8<=len(b):
      uid=struct.unpack_from('<I',b,at+4)[0]
      if uid<65536:rows.append({'elf':name,'name':label,'candidate_uid':uid,'table_offset':at})
     at+=4
out=Path(__file__).resolve().parent.parent/'kyf37-rom/felica-stock-uid-candidates.json'
out.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
