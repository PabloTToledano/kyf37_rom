"""Append permissions to binary Android XML without changing existing indices."""
import struct
U32=lambda b,p:struct.unpack_from('<I',b,p)[0]
def add_permissions(data,permissions,activity=None):
 b=data;pos=8
 while U32(b,pos)&65535!=1:pos+=U32(b,pos+4)
 kind,header,size=struct.unpack_from('<HHI',b,pos);count,styles,flags,start,end=struct.unpack_from('<5I',b,pos+8)
 assert styles==0;utf8=bool(flags&256)
 def length(at):
  if utf8:
   n=b[at];return (((n&127)<<8)|b[at+1],at+2) if n&128 else (n,at+1)
  n=struct.unpack_from('<H',b,at)[0];assert n<32768;return n,at+2
 strings=[]
 for i in range(count):
  at=pos+start+U32(b,pos+header+4*i);n,at=length(at)
  if utf8:n,at=length(at)
  strings.append(b[at:at+n*(1 if utf8 else 2)].decode('utf-8' if utf8 else 'utf-16le'))
 def index(value):
  if value not in strings:strings.append(value)
  return strings.index(value)
 uri=index('http://schemas.android.com/apk/res/android');node=index('uses-permission')
 tail=b[pos+size:];at=0;name=None;insert=None
 while at<len(tail):
  typ,head,sz=struct.unpack_from('<HHI',tail,at)
  if typ==0x180:
   for i in range((sz-head)//4):
    if U32(tail,at+head+4*i)==0x01010003:name=i
  if typ==0x102 and strings[U32(tail,at+head+4)]=='application':insert=at;break
  at+=sz
 assert name is not None and insert is not None
 chunks=b''
 for permission in permissions:
  if permission in strings:continue
  value=index(permission)
  chunks+=struct.pack('<HHIII',0x102,16,56,0,0xffffffff)+struct.pack('<IIHHHHHH',0xffffffff,node,20,20,1,0,0,0)+struct.pack('<IIIHBBI',uri,name,value,8,0,3,value)
  chunks+=struct.pack('<HHIIIII',0x103,16,24,0,0xffffffff,0xffffffff,node)
 tail=tail[:insert]+chunks+tail[insert:]
 if activity:
  activityNode=index('activity');activityValue=index(activity)
  at=0
  while at<len(tail):
   typ,head,sz=struct.unpack_from('<HHI',tail,at)
   if typ==0x103 and strings[U32(tail,at+head+4)]=='application':break
   at+=sz
  assert at<len(tail)
  # No intent filter: this screen is launched only with an explicit app intent.
  addition=struct.pack('<HHIII',0x102,16,56,0,0xffffffff)+struct.pack('<IIHHHHHH',0xffffffff,activityNode,20,20,1,0,0,0)+struct.pack('<IIIHBBI',uri,name,activityValue,8,0,3,activityValue)
  addition+=struct.pack('<HHIIIII',0x103,16,24,0,0xffffffff,0xffffffff,activityNode)
  tail=tail[:at]+addition+tail[at:]
 def enc_len(n):return bytes([n]) if n<128 else bytes([128|(n>>8),n&255])
 offsets=[];payload=b''
 for text in strings:
  raw=text.encode('utf-8' if utf8 else 'utf-16le');offsets.append(len(payload))
  payload+=(enc_len(len(text))+enc_len(len(raw))+raw+b'\0') if utf8 else struct.pack('<H',len(raw)//2)+raw+b'\0\0'
 payload+=b'\0'*((-len(payload))%4);start=header+4*len(strings)
 pool=struct.pack('<HHI5I',1,header,start+len(payload),len(strings),0,flags,start,0)+b''.join(struct.pack('<I',x) for x in offsets)+payload
 result=b[:pos]+pool+tail
 return result[:4]+struct.pack('<I',len(result))+result[8:]
