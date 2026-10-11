"""Resource-ID compatibility for Android 5 OEM APK -> Android 10 (no resource-name guessing)."""
import struct,re,subprocess
from pathlib import Path
U16=lambda b,o:struct.unpack_from('<H',b,o)[0]
U32=lambda b,o:struct.unpack_from('<I',b,o)[0]
def resource_names(p,aapt):
 s=subprocess.check_output([str(aapt),'dump','resources',str(p)],text=True)
 return {int(i,16):n for i,n in re.findall(r'resource (0x[0-9a-f]+) (\S+)',s)}
def framework_map(old,new,aapt):
 before=resource_names(old,aapt);after={n:i for i,n in resource_names(new,aapt).items()}
 return {i:after[n] for i,n in before.items() if n in after and after[n]!=i}
def remap_binary(data,ids):
 b=bytearray(data)
 def word(pos):
  value=U32(b,pos)
  if value in ids:struct.pack_into('<I',b,pos,ids[value])
 def value(pos):
  if b[pos+3] in (1,2):word(pos+4)
 def chunk(pos,end):
  while pos<end:
   typ,head,size=struct.unpack_from('<HHI',b,pos)
   if size<8 or pos+size>end:raise ValueError('Invalid resource chunk')
   if typ==2 or typ==3:chunk(pos+head,pos+size)
   elif typ==0x200:chunk(pos+head,pos+size)
   elif typ==0x102:
    ext=pos+head;attrStart=U16(b,ext+8);attrSize=U16(b,ext+10);count=U16(b,ext+12)
    for i in range(count):value(ext+attrStart+i*attrSize+12)
   elif typ==0x180:
    for at in range(pos+head,pos+size,4):word(at)
   elif typ==0x201:
    flags=b[pos+9];count=U32(b,pos+12);start=U32(b,pos+16)
    assert flags==0,'Sparse resource type needs explicit support'
    for i in range(count):
     offset=U32(b,pos+head+4*i)
     if offset==0xffffffff:continue
     entry=pos+start+offset;entrySize=U16(b,entry);entryFlags=U16(b,entry+2)
     if entryFlags&1:
      word(entry+8);n=U32(b,entry+12)
      for j in range(n):word(entry+entrySize+12*j);value(entry+entrySize+12*j+4)
     else:value(entry+entrySize)
   pos+=size
 chunk(0,len(b));return bytes(b)
