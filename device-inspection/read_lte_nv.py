"""Read-only Qualcomm NV query; records complete response frames for inspection."""
import binascii,json,struct,time,sys,socket
from pathlib import Path
import usb.core
from native_winusb import DiagnosticUSB
def crc(data):
    value=0xffff
    for b in data:
        value^=b
        for _ in range(8): value=(value>>1)^(0x8408 if value&1 else 0)
    return value^0xffff
def frame(data):
    data+=struct.pack('<H',crc(data))
    return b''.join(bytes((0x7d,b^0x20)) if b in (0x7d,0x7e) else bytes((b,)) for b in data)+b'\x7e'
def decode(data):
    out=bytearray();escaped=False
    for b in data:
        if escaped:out.append(b^0x20);escaped=False
        elif b==0x7d:escaped=True
        else:out.append(b)
    if len(out)<3 or crc(out[:-2])!=int.from_bytes(out[-2:],'little'):return None
    return bytes(out[:-2])
class DiagTCP:
    def __init__(self):
        self.s=socket.create_connection(('127.0.0.1',43555),timeout=3)
    def write(self,endpoint,data,timeout):self.s.sendall(data)
    def read(self,endpoint,size,timeout):
        self.s.settimeout(timeout/1000)
        try:return self.s.recv(size)
        except socket.timeout:raise usb.core.USBTimeoutError('TCP read timeout')
    def close(self):self.s.close()
records=[]
device=DiagTCP() if '--tcp' in sys.argv else DiagnosticUSB()
try:
    for item in (6828,65633):
        if item>65535:continue
        payload=b'\x26'+struct.pack('<H',item)+bytes(130)
        device.write(0x01,frame(payload),timeout=2000)
        pending=bytearray();seen=[];deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            try:pending.extend(device.read(0x81,16384,timeout=500))
            except usb.core.USBTimeoutError:continue
            while 0x7e in pending:
                end=pending.index(0x7e);p=decode(pending[:end]);del pending[:end+1]
                if p is None:continue
                if len(seen)<30:seen.append(p.hex())
                if p[0]==0x26 and len(p)>=133 and int.from_bytes(p[1:3],'little')==item:
                    value=int.from_bytes(p[3:11],'little')
                    records.append({'item':item,'status':int.from_bytes(p[131:133],'little'),
                                    'raw':p.hex(),'lte_mask_hex':hex(value),
                                    'bands':[i+1 for i in range(64) if value&(1<<i)]})
                    deadline=0
            if deadline==0:break
        if not records or records[-1]['item']!=item:records.append({'item':item,'responses':seen,'no_valid_nv_response':True})
finally:device.close()
out=Path(__file__).resolve().parent/('lte-nv-tcp-original.json' if '--tcp' in sys.argv else 'lte-nv-original.json')
out.write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
