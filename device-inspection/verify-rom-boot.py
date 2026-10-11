"""Inspect a boot candidate without flashing or extracting archive paths."""
from pathlib import Path
import struct,gzip,hashlib,json,argparse
root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('source',nargs='?',type=Path,default=root/'kyf37-rom/boot-lineage-feedback-candidate.img')
parser.add_argument('--expected-kernel',type=Path,help='Require this exact rebuilt kernel instead of the stock kernel.')
parser.add_argument('--kernel-policy-max',type=int,help='Require any embedded binary SELinux policy to fit the verified kernel maximum.')
parser.add_argument('--require-legacy-first-stage',action='store_true',help='Validate the Android 10 legacy-system early mount and full rootfs ramdisk.')
parser.add_argument('--report',type=Path,default=root/'kyf37-rom/boot-candidate-inspection.json')
args=parser.parse_args()
source=args.source
stock=root/'phone-backup/pre-rom-20261007/boot.img'
def unpack(path):
    data=path.read_bytes();assert data[:8]==b'ANDROID!'
    fields=struct.unpack_from('<10I',data,8)
    page=fields[7];assert page in (2048,4096,8192,16384)
    offset=page;blobs={}
    for name,size in zip(('kernel','ramdisk','second','dt'),(fields[0],fields[2],fields[4],fields[8])):
        blobs[name]=data[offset:offset+size];assert len(blobs[name])==size
        offset+=(size+page-1)//page*page
    return data,fields,blobs
data,fields,blobs=unpack(source)
boot_id=hashlib.sha1()
for name in ('kernel','ramdisk','second','dt'):
    boot_id.update(blobs[name]);boot_id.update(struct.pack('<I',len(blobs[name])))
assert data[576:596]==boot_id.digest(), 'Legacy boot image SHA1 ID does not match packaged payloads'
_,stock_fields,stock_blobs=unpack(stock)
expected_kernel=args.expected_kernel.read_bytes() if args.expected_kernel else stock_blobs['kernel']
assert blobs['kernel']==expected_kernel,'Packaged kernel differs from the selected verified kernel'
assert len(data)<=16777216,'Boot image exceeds its actual partition'
def dt_entries(blob):
    assert blob[:4]==b'QCDT'
    version,count=struct.unpack_from('<2I',blob,4);assert version==3
    result=[]
    for i in range(count):
        fields=struct.unpack_from('<10I',blob,12+i*40)
        offset,size=fields[8:10]
        payload=blob[offset:offset+size];assert len(payload)==size
        result.append((fields[:8],payload))
    return result
original=dt_entries(stock_blobs['dt'])
selected=dt_entries(blobs['dt'])
assert len(selected)==6
assert all(identity[0]==245 and identity[1]==8 for identity,_ in selected)
assert all(entry in original for entry in selected),'Device-tree payload/identity differs from OEM'
assert fields[1:8:2]==stock_fields[1:8:2],'Unexpected boot address/page geometry'
archive=gzip.decompress(blobs['ramdisk']);entries={};pos=0
while pos+110<=len(archive):
    assert archive[pos:pos+6] in (b'070701',b'070702')
    header=[int(archive[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
    size,namesize=header[6],header[11]
    name=archive[pos+110:pos+110+namesize-1].decode()
    start=(pos+110+namesize+3)&~3
    entries[name]=archive[start:start+size]
    assert len(entries[name])==size
    if name=='TRAILER!!!':break
    pos=(start+size+3)&~3
assert 'init' in entries and 'init.environ.rc' in entries and 'fstab.qcom' in entries
assert b'export BOOTCLASSPATH' in entries['init.environ.rc']
assert b'forceencrypt=' not in entries['fstab.qcom']
assert b'import /init.kc.model.rc' in entries['init.qcom.rc']
assert 'install-recovery.sh' not in entries
if args.require_legacy_first_stage:
    early=entries['fstab.kyf37.first_stage'].decode().splitlines()
    assert len(early)==1
    columns=early[0].split()
    assert columns==['/dev/block/bootdevice/by-name/system','/system','ext4','ro,barrier=1','wait,first_stage_mount']
    init=entries['init']
    assert init[:5]==b'\x7fELF\x01' and struct.unpack_from('<H',init,18)[0]==40
    phoff=struct.unpack_from('<I',init,28)[0]
    phsize,phnum=struct.unpack_from('<HH',init,42)
    assert all(struct.unpack_from('<I',init,phoff+i*phsize)[0]!=3 for i in range(phnum)), 'Early init must have no dynamic interpreter'
    assert b'/fstab.kyf37.first_stage' in init
    assert b'/dev/graphics/fb1 0660 system graphics' in entries['ueventd.qcom.rc']
    assert all(name in entries for name in ('init.rc','sepolicy','ueventd.rc','init.zygote32.rc'))
policy_version=struct.unpack_from('<I',entries['sepolicy'],16)[0] if 'sepolicy' in entries else None
if policy_version is not None and args.kernel_policy_max is not None:
    assert policy_version<=args.kernel_policy_max,('Kernel cannot load packaged SELinux policy',policy_version,args.kernel_policy_max)
report={'candidate_sha256':hashlib.sha256(data).hexdigest(),
        'stock_kernel_preserved':blobs['kernel']==stock_blobs['kernel'],
        'selected_kernel_sha256':hashlib.sha256(blobs['kernel']).hexdigest(),
        'selected_kernel_verified':True,'stock_dt_payloads_preserved':True,
        'legacy_boot_id_verified':True,
        'legacy_first_stage_verified':args.require_legacy_first_stage,
        'ramdisk_policy_version':policy_version,'verified_kernel_policy_max':args.kernel_policy_max,
        'dt_selection':{'original_count':len(original),'selected_count':len(selected),
                        'identities':[list(identity) for identity,_ in selected]},
        'boot_geometry_preserved':True,'ramdisk_entries':sorted(entries),
        'cmdline':data[64:576].split(b'\0')[0].decode(),
        'scope':'Boot layout, exact selected kernel, OEM DT and selected ramdisk invariants; actual boot is unverified.'}
args.report.write_text(json.dumps(report,indent=2)+'\n')
print('Selected kernel, OEM DT, boot geometry and selected Android ramdisk invariants verified.')
