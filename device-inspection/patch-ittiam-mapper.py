from pathlib import Path
import struct,hashlib,json,subprocess

host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
source=Path('/home/pablo/kyf37-rom/stock-system/vendor/lib/libOmxIttiamVdec.so')
original=source.read_bytes();data=bytearray(original)
assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',data,18)[0]==40
shoff=struct.unpack_from('<I',data,32)[0]
entsize,count,names_index=struct.unpack_from('<HHH',data,46)
assert entsize==40
sections=[struct.unpack_from('<10I',data,shoff+i*entsize) for i in range(count)]
names=sections[names_index];strings=data[names[4]:names[4]+names[5]]
def name(s):return bytes(strings[s[0]:]).split(b'\x00',1)[0]
dynstr=[s for s in sections if name(s)==b'.dynstr']
assert len(dynstr)==1
section=dynstr[0];start,size=section[4:6]
old=b'_ZN7android19GraphicBufferMapper4lockEPK13native_handleiRKNS_4RectEPPv\x00'
new=old.replace(b'native_handlei',b'native_handlej')
assert len(old)==len(new) and bytes(data[start:start+size]).count(old)==1
offset=start+bytes(data[start:start+size]).index(old)
data[offset:offset+len(old)]=new
assert sum(a!=b for a,b in zip(original,data))==1
out=host/'patched-vendor/libOmxIttiamVdec.so';out.parent.mkdir(exist_ok=True)
out.write_bytes(data)
symbols=subprocess.check_output(['readelf','--dyn-syms','-W',str(out)],text=True)
assert old[:-1].decode() not in symbols and new[:-1].decode() in symbols
(out.parent/'ittiam-mapper-patch.json').write_text(json.dumps({
 'source':'vendor/lib/libOmxIttiamVdec.so','original_sha256':hashlib.sha256(original).hexdigest(),
 'patched_sha256':hashlib.sha256(data).hexdigest(),'old_symbol':old[:-1].decode(),
 'new_symbol':new[:-1].decode(),'dynstr_offset':offset,'changed_bytes':1,
 'reason':'Android7/8 GraphicBufferMapper lock usage changed int to uint32_t. ARM32 argument width/bitmask representation and other parameters unchanged. Retarget only the imported symbol; no instruction/layout changes.',
 'note':'Static import correction only; codec/runtime and complete vendor buffer ABI still require device validation.'},indent=2))
print('Retargeted one mapper import in candidate codec; original blob unchanged')
