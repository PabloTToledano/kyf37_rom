#!/usr/bin/env python3
"""Swap the kernel blob (and optionally patch ramdisk files) of a legacy QCDT boot image (run in WSL).
usage: base_unsigned.img zImage out_unsigned.img
Ramdisk patches applied: fstab.qcom SD-slot glob (same as fix-android10-fstab-sdcard.py)."""
import struct, sys, gzip
from pathlib import Path
base, kern, out = map(Path, sys.argv[1:4])
d = base.read_bytes(); assert d[:8] == b'ANDROID!'
f = list(struct.unpack_from('<10I', d, 8)); page = f[7]; assert page == 2048
pos = page; blobs = []
for size in [f[0], f[2], f[4], f[8]]:
    blobs.append(d[pos:pos+size]); pos += (size+page-1)//page*page
k = kern.read_bytes(); print('old kernel', len(blobs[0]), 'new', len(k))
blobs[0] = k
# ramdisk: gunzip -> parse newc cpio (pure python, no cpio binary needed) -> patch -> rewrite -> gzip
def cpio_parse(buf):
    ents = []; i = 0
    while True:
        assert buf[i:i+6] == b'070701', 'not newc'
        hdr = [int(buf[i+6+8*j:i+14+8*j], 16) for j in range(13)]
        ino, mode, uid, gid, nlink, mtime, fsize, dmaj, dmin, rmaj, rmin, nsize, chk = hdr
        name = buf[i+110:i+110+nsize-1].decode()
        o = (i + 110 + nsize + 3) & ~3
        data = buf[o:o+fsize]
        i = (o + fsize + 3) & ~3
        if name == 'TRAILER!!!':
            return ents
        ents.append([ino, mode, uid, gid, nlink, mtime, dmaj, dmin, rmaj, rmin, name, data])
def cpio_write(ents):
    out = bytearray()
    def pad():
        while len(out) % 4: out.append(0)
    for n, (ino, mode, uid, gid, nlink, mtime, dmaj, dmin, rmaj, rmin, name, data) in enumerate(ents + [[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 'TRAILER!!!', b'']]):
        nb = name.encode() + bytes([0])
        fields = [ino, mode, uid, gid, nlink, mtime, len(data), dmaj, dmin, rmaj, rmin, len(nb), 0]
        out += b'070701' + b''.join(b'%08X' % x for x in fields) + nb
        pad(); out += data; pad()
    return bytes(out)
ents = cpio_parse(gzip.decompress(blobs[1]))
for e in ents:
    if e[10] == 'fstab.qcom':
        s = e[11].decode()
        if '7864900.sdhci/mmc_host* ' not in s:
            assert '7864900.sdhci/mmc_host ' in s
            e[11] = s.replace('7864900.sdhci/mmc_host ', '7864900.sdhci/mmc_host* ').encode()
            print('patched ramdisk fstab.qcom')
for e in ents:
    if e[10] == 'init.kyf37.diagnostic.rc':
        t = e[11].decode()
        if 'dalvik.vm.usejit false' in t:
            e[11] = t.replace('dalvik.vm.usejit false', 'dalvik.vm.usejit true').replace('dalvik.vm.usejitprofiles false', 'dalvik.vm.usejitprofiles true').encode()
            print('ramdisk: JIT enabled')
blobs[1] = gzip.compress(cpio_write(ents), compresslevel=9, mtime=0)
h = bytearray(d[:page])
struct.pack_into('<I', h, 8, len(blobs[0]))
struct.pack_into('<I', h, 16, len(blobs[1]))
h[576:608] = b'\0'*32
r = bytes(h) + b''.join(b + bytes((-len(b)) % page) for b in blobs)
assert len(r) <= 16777216, len(r)
out.write_bytes(r); print('wrote', out, len(r))
