"""Reconstruct documented KYF37 vendor A3 reads / guarded misc-only A1 request.

Default: inspect only. --request-recovery writes precisely three misc sectors
after live GPT CRC/geometry and enrolled recovery/keystore checks.
No programmer uploads, USB reset, image flash, or other disk writes.
"""
from pathlib import Path
import argparse, struct, json, hashlib, zlib, datetime
import usb.core, usb.util, usb.backend.libusb1
try:
    import libusb_package
except ImportError:
    libusb_package=None

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--request-recovery',action='store_true')
args=parser.parse_args()
folder=root/'kyf37-rom'/('vendor-recovery-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
folder.mkdir(exist_ok=False)
backend=usb.backend.libusb1.get_backend(find_library=libusb_package.find_library) if libusb_package else usb.backend.libusb1.get_backend()
dev=usb.core.find(idVendor=0x0482,idProduct=0x0a7f,backend=backend)
assert dev is not None, 'KYF37 download USB 0482:0a7f is not connected'
cfg=dev.get_active_configuration()
matches=[i for i in cfg if any(e.bEndpointAddress==0x01 for e in i) and any(e.bEndpointAddress==0x81 for e in i)]
assert len(matches)==1, 'Ambiguous vendor USB interface'
interface=matches[0].bInterfaceNumber
usb.util.claim_interface(dev,interface)
def send(data):
    assert dev.write(0x01,data,timeout=5000)==len(data)
def receive(size):
    return bytes(dev.read(0x81,size,timeout=5000))
def frame(command,*values):return struct.pack('<'+'I'*(2+len(values)),command,8+len(values)*4,*values)
def read(lba,size):
    assert size>0 and size%512==0
    result=bytearray()
    for offset in range(0,size,0x3e00):
        count=min(0x3e00,size-offset);sector=lba+offset//512
        send(frame(0xa3,sector,count))
        reply=receive(count+16)
        assert len(reply)==count+16,(hex(sector),'short vendor response',len(reply),count)
        assert struct.unpack_from('<4I',reply)==(0xa4,count+16,sector,count)
        result.extend(reply[16:])
    return bytes(result)
def sha(data):return hashlib.sha256(data).hexdigest()
try:
    # Drain the initial hello first: this controller can hold OUT transfers
    # until the pending IN hello has been consumed. No USB reset is used.
    try:
        pending=bytes(dev.read(0x81,512,timeout=1000))
    except usb.core.USBTimeoutError:
        pending=None
        send(frame(0x0c,3))
    for attempt in range(4):
        reply=pending if pending is not None else receive(512)
        pending=None
        command,length=struct.unpack_from('<2I',reply)
        assert length==len(reply)
        if command==1:
            assert length==48 and struct.unpack_from('<I',reply,8)[0]==2
            send(struct.pack('<12I',2,48,2,1,0,3,0,0,0,0,0,0))
        elif command==0x0b:
            assert length==8
            break
        else:raise AssertionError(('Unexpected Sahara frame',command,length))
    else:raise AssertionError('No command-ready response')
    print('Command mode ready; reading live GPT',flush=True)
    first=read(0,34*512);(folder/'gpt-first-34-sectors.bin').write_bytes(first)
    header=bytearray(first[512:1024]);assert header[:8]==b'EFI PART'
    hsize,hcrc=struct.unpack_from('<2I',header,12);assert 92<=hsize<=512
    struct.pack_into('<I',header,16,0);assert zlib.crc32(header[:hsize])&0xffffffff==hcrc
    current,backup=struct.unpack_from('<2Q',header,24)
    assert current==1 and backup==15269887
    table_lba,count,entry_size,table_crc=struct.unpack_from('<Q3I',header,72)
    assert table_lba==2 and count<=128 and entry_size==128
    table=first[table_lba*512:table_lba*512+count*entry_size]
    assert len(table)==count*entry_size and zlib.crc32(table)&0xffffffff==table_crc
    live={}
    for index in range(count):
        entry=table[index*entry_size:(index+1)*entry_size]
        if not any(entry[:16]):continue
        start,end=struct.unpack_from('<2Q',entry,32)
        name=entry[56:128].decode('utf-16le').split('\0')[0]
        assert name and name not in live and end>=start
        live[name]={'number':index+1,'start_lba':start,'end_lba':end,'bytes':(end-start+1)*512}
    expected=json.loads((root/'phone-backup/partition-map.json').read_text())['partitions']
    assert set(live)=={p['name'] for p in expected}
    for p in expected:
        assert live[p['name']]=={k:p[k] for k in ['number','start_lba','end_lba','bytes']},p['name']
    (folder/'live-partitions.json').write_text(json.dumps(live,indent=2)+'\n')
    hashes={}
    for part,want in [('recovery','9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e'),
                      ('keystore','0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c')]:
        print('Reading and verifying '+part,flush=True)
        data=read(live[part]['start_lba'],live[part]['bytes'])
        (folder/(part+'.img')).write_bytes(data)
        hashes[part]=sha(data);assert hashes[part]==want,('Live enrolled image differs',part,hashes[part])
    assert live['misc']['start_lba']==15022080
    before=read(live['misc']['start_lba'],1536);(folder/'misc-before.bin').write_bytes(before)
    report={'partition_geometry_verified':True,'gpt_crcs_verified':True,'hashes':hashes,'misc_written':False}
    if args.request_recovery:
        command=before[:32].split(b'\0')[0]
        assert command in (b'',b'boot-recovery'),('Unexpected existing misc command',command)
        after=bytearray(before);after[:1088]=bytes(1088)
        after[:13]=b'boot-recovery';after[64:73]=b'recovery\n'
        assert after[1088:]==before[1088:]
        assert read(live['misc']['start_lba'],1536)==before,'Misc changed since snapshot'
        (folder/'misc-request.bin').write_bytes(after)
        print('Writing only three verified misc sectors for recovery entry',flush=True)
        send(struct.pack('<4I',0xa1,16+1536,live['misc']['start_lba'],1536)+after)
        reply=receive(512)
        assert reply==frame(0xa2,live['misc']['start_lba'],1536)
        actual=read(live['misc']['start_lba'],1536)
        (folder/'misc-readback.bin').write_bytes(actual)
        assert actual==after,'Recovery request readback differs'
        report['misc_written']=True;report['misc_readback_verified']=True
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'evidence':str(folder),**report}),flush=True)
finally:
    usb.util.release_interface(dev,interface)
    usb.util.dispose_resources(dev)
