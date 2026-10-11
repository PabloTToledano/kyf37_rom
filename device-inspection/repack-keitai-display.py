#!/usr/bin/env python3
"""Swap the KYF37 display-fix libminuitwrp.so (device-inspection/libminuitwrp-fbdev.so, md5 6bced108...) into the
unsigned keitai recovery image. The first keitai build used the stock TWRP minui build, which leaves this panel on the
bootloader 'GRATINA / Loading...' splash (the recovery runs, adb works, nothing is drawn). The old working TWRP image
has exactly this library. Pure-Python boot image + newc cpio rewrite (header v0, page 2048); sign afterwards with
sign-keitai-recovery.py. Idempotent: the output is rebuilt from the input every time.
usage: repack-keitai-display.py [in-unsigned.img [out-unsigned.img]]"""
import gzip, hashlib, struct, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'kyf37-twrp-device/keitai/kyf37-keitai-recovery-unsigned.img'
dst = Path(sys.argv[2]) if len(sys.argv) > 2 else root / 'kyf37-twrp-device/keitai/kyf37-keitai-recovery-unsigned-dispfix.img'
lib = (root / 'device-inspection/libminuitwrp-fbdev.so').read_bytes()
assert hashlib.md5(lib).hexdigest().startswith('6bced108'), 'unexpected display-fix library'
TARGET = 'sbin/libminuitwrp.so'

d = bytearray(src.read_bytes())
assert d[:8] == b'ANDROID!'
ks, ka, rs, ra, ss, sa, ta, page, dts = struct.unpack_from('<9I', d, 8)
pad = lambda n: ((n + page - 1) // page) * page
k_off = page
r_off = page + pad(ks)
kernel = bytes(d[k_off:k_off + ks])
ramdisk_gz = bytes(d[r_off:r_off + rs])
second_off = r_off + pad(rs)
second = bytes(d[second_off:second_off + ss])
dt_off = second_off + pad(ss)
dt = bytes(d[dt_off:dt_off + dts])

raw = gzip.decompress(ramdisk_gz)
out = bytearray()
p = 0
replaced = False
while p + 110 <= len(raw):
    assert raw[p:p + 6] == b'070701'
    fields = [int(raw[p + 6 + 8 * i:p + 14 + 8 * i], 16) for i in range(13)]
    namesz, filesz = fields[11], fields[6]
    name_end = p + 110 + namesz
    name = raw[p + 110:name_end - 1].decode()
    data_start = (name_end + 3) & ~3
    data = raw[data_start:data_start + filesz]
    nxt = (data_start + filesz + 3) & ~3
    if name == TARGET:
        data = lib
        fields[6] = len(lib)
        replaced = True
    hdr = b'070701' + b''.join(('%08X' % v).encode() for v in fields)
    out += hdr + raw[p + 110:name_end]
    out += b'\0' * (((len(out) + 3) & ~3) - len(out))
    out += data
    out += b'\0' * (((len(out) + 3) & ~3) - len(out))
    p = nxt
    if name == 'TRAILER!!!':
        break
assert replaced, TARGET + ' not found in ramdisk'
out += b'\0' * (((len(out) + 255) & ~255) - len(out))  # keep the cpio 256-aligned like the original tail
new_gz = gzip.compress(bytes(out), compresslevel=9, mtime=0)

sha = hashlib.sha1()
sha.update(kernel); sha.update(struct.pack('<I', ks))
sha.update(new_gz); sha.update(struct.pack('<I', len(new_gz)))
sha.update(second); sha.update(struct.pack('<I', ss))
if dts:
    sha.update(dt); sha.update(struct.pack('<I', dts))
hdr = bytearray(d[:page])
struct.pack_into('<I', hdr, 16, len(new_gz))
hdr[576:576 + 32] = sha.digest() + b'\0' * 12

img = bytearray(hdr)
img += kernel + b'\0' * (pad(ks) - ks)
img += new_gz + b'\0' * (pad(len(new_gz)) - len(new_gz))
img += second + b'\0' * (pad(ss) - ss)
img += dt + b'\0' * (pad(dts) - dts)
assert len(img) <= 16 * 1024 * 1024 - 8192, 'no room left for the signature'
dst.write_bytes(img)
print('wrote', dst, len(img), 'bytes; ramdisk gz', len(ramdisk_gz), '->', len(new_gz), '; lib md5 6bced108 swapped in')
