"""Extend the original, migrated Kyocera APK without changing its resources or original DEX."""
from pathlib import Path
import struct,zipfile,re,runpy,json,hashlib,copy
here=Path(__file__).resolve().parent;tree=Path('/home/pablo/kyf37-android10')
base=here.parent/'kyf37-rom/all-stock-app-ports/signed-apks/Kyf37StockDataFolder.apk'
payload=tree/'out/target/product/kyf37/system/app/Kyf37GalleryCode/Kyf37GalleryCode.apk'
if not payload.exists():payload=tree/'out/target/product/kyf37/obj/APPS/Kyf37GalleryCode_intermediates/package.apk'
dest=tree/'packages/apps/Kyf37RemainingStockApps/Kyf37StockDataFolder.apk'
old='jp.kyocera.datafolder.activity.DataFolderActivity';new='org.kyf37.gallery.GalleryActivity'
def modern_manifest(data):
    pos=8
    while struct.unpack_from('<H',data,pos)[0]!=1:pos+=struct.unpack_from('<I',data,pos+4)[0]
    kind,header,size=struct.unpack_from('<HHI',data,pos)
    count,styles,flags,start,end=struct.unpack_from('<5I',data,pos+8)
    assert styles==0
    utf8=bool(flags&256)
    def length(at):
        if utf8:
            n=data[at];return (((n&127)<<8)|data[at+1],at+2) if n&128 else (n,at+1)
        n=struct.unpack_from('<H',data,at)[0]
        if n&0x8000:return ((n&0x7fff)<<16)|struct.unpack_from('<H',data,at+2)[0],at+4
        return n,at+2
    strings=[]
    for i in range(count):
        at=pos+start+struct.unpack_from('<I',data,pos+header+i*4)[0];n,at=length(at)
        if utf8:n,at=length(at)
        strings.append(data[at:at+n*(1 if utf8 else 2)].decode('utf-8' if utf8 else 'utf-16le'))
    assert old in strings and new not in strings
    strings[strings.index(old)]=new
    gallery=len(strings);strings.append('Gallery')
    tail=bytearray(data[pos+size:]);at=0;patched=False
    while at<len(tail):
        typ,head,sz=struct.unpack_from('<HHI',tail,at)
        if typ==0x102:
            node=struct.unpack_from('<I',tail,at+head+4)[0]
            attr_start,attr_size,attr_count=struct.unpack_from('<HHH',tail,at+head+8)
            attrs=[at+head+attr_start+i*attr_size for i in range(attr_count)]
            if strings[node]=='activity' and any(strings[struct.unpack_from('<I',tail,a+4)[0]]=='name' and tail[a+15]==3 and strings[struct.unpack_from('<I',tail,a+16)[0]]==new for a in attrs):
                for a in attrs:
                    name=strings[struct.unpack_from('<I',tail,a+4)[0]]
                    if name=='label':struct.pack_into('<I',tail,a+8,gallery);tail[a+15]=3;struct.pack_into('<I',tail,a+16,gallery);patched=True
                    if name=='stateNotNeeded':struct.pack_into('<I',tail,a+16,0)
        at+=sz
    assert patched,'original launcher label not found'
    def enc(n):return bytes([n]) if n<128 else bytes([128|(n>>8),n&255])
    offsets=[];raw=b''
    for s in strings:
        b=s.encode('utf-8' if utf8 else 'utf-16le');offsets.append(len(raw));units=len(s.encode('utf-16le'))//2
        raw+=(enc(units)+enc(len(b))+b+b'\0') if utf8 else struct.pack('<H',units)+b+b'\0\0'
    raw+=b'\0'*((-len(raw))%4);start=header+4*len(strings)
    pool=struct.pack('<HHI5I',1,header,start+len(raw),len(strings),0,flags&~1,start,0)+b''.join(struct.pack('<I',n) for n in offsets)+raw
    out=data[:pos]+pool+tail;out=out[:4]+struct.pack('<I',len(out))+out[8:]
    return runpy.run_path(str(here/'stock-manifest-compat.py'))['add_permissions'](out,['android.permission.READ_EXTERNAL_STORAGE'],activity=old)
with zipfile.ZipFile(base) as stock,zipfile.ZipFile(payload) as code:
    dex=[n for n in code.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
    assert len(dex)==1,'payload must be a single DEX'
    indices=[int(re.search(r'classes(\d*)\.dex',n)[1] or '1') for n in stock.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
    next_dex='classes'+str(max(indices)+1)+'.dex'
    temp=dest.with_suffix('.gallery.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as out:
        for entry in stock.infolist():
            if entry.filename.startswith('META-INF/'):continue
            value=stock.read(entry.filename)
            if entry.filename=='AndroidManifest.xml':value=modern_manifest(value)
            out.writestr(copy.copy(entry),value)
        dex_entry=zipfile.ZipInfo(next_dex,(2009,1,1,0,0,0));dex_entry.compress_type=zipfile.ZIP_DEFLATED
        out.writestr(dex_entry,code.read('classes.dex'))
    if dest.exists() and dest.read_bytes()==temp.read_bytes():temp.unlink()
    else:temp.replace(dest)
    with zipfile.ZipFile(dest) as merged:
        preserved=[n for n in stock.namelist() if n!='AndroidManifest.xml' and not n.startswith('META-INF/')]
        assert all(stock.read(n)==merged.read(n) for n in preserved)
    report={'base':str(base),'output':str(dest),'package':'jp.kyocera.datafolder','launcher':new,'legacy_activity':old,
            'preserved_original_entries':len(preserved),'original_dex_unchanged':True,'resources_unchanged':True,'new_dex':next_dex,
            'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'payload_sha256':hashlib.sha256(code.read('classes.dex')).hexdigest()}
    (here.parent/'kyf37-rom/gallery-port-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('Extended original Data Folder:',len(preserved),'original entries unchanged;',next_dex,'added')
