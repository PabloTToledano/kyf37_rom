import struct, gzip, zlib, sys, hashlib
def unpack(path):
    d = open(path,'rb').read()
    # android boot header v0: magic, kernel_size, kernel_addr, ramdisk_size, ...
    ksz, kaddr, rsz = struct.unpack_from('<III', d, 8)
    page = struct.unpack_from('<I', d, 36)[0]
    off = page + ((ksz + page - 1)//page)*page
    rd = d[off:off+rsz]
    raw = gzip.decompress(rd) if rd[:2]==b'\x1f\x8b' else rd
    files = {}
    p = 0
    while p+110 <= len(raw):
        assert raw[p:p+6] == b'070701', raw[p:p+6]
        f = [int(raw[p+6+8*i:p+14+8*i],16) for i in range(13)]
        namesz, filesz = f[11], f[6]
        name = raw[p+110:p+110+namesz-1].decode(errors='replace')
        p = (p+110+namesz+3)&~3
        data = raw[p:p+filesz]; p = (p+filesz+3)&~3
        if name == 'TRAILER!!!': break
        files[name] = (filesz, hashlib.md5(data).hexdigest()[:8], data)
    return files, ksz
old, ok = unpack('kyf37-twrp-device/kyf37-twrp-owner-signed.img')
new, nk = unpack('kyf37-twrp-device/keitai/kyf37-keitai-recovery-owner-signed.img')
print('kernel sizes', ok, nk, 'files', len(old), len(new))
for n in sorted(set(old)|set(new)):
    a = old.get(n); b = new.get(n)
    if a is None: print('NEW only :', n, b[0])
    elif b is None: print('OLD only :', n, a[0])
    elif a[1] != b[1] and not n.startswith('twres/'): print('DIFF     :', n, a[0], '->', b[0])
