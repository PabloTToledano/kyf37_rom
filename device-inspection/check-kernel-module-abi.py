#!/usr/bin/env python3
"""Verify that out-of-tree kernel modules match the kernel they will run on (run in WSL).
usage: check-kernel-module-abi.py <kernel_build_dir_with_Module.symvers> <module.ko> [<module.ko> ...]
For every module: vermagic must equal the kernel's, and every CRC in its __versions section must match Module.symvers.
Exit 1 on any mismatch. This is the failure that broke Wi-Fi on 2026-10-09 ('wlan: disagrees about version of symbol module_layout')."""
import sys, struct, os
build = sys.argv[1]
syms = {}
for fn in ('Module.symvers',):
    for line in open(os.path.join(build, fn), errors='ignore'):
        p = line.split()
        if len(p) >= 2:
            syms[p[1]] = int(p[0], 16)
# kernel vermagic from the generated header
vm = None
hdr = os.path.join(build, 'include/generated/utsrelease.h')
rel = open(hdr).read().split('"')[1] if os.path.exists(hdr) else None
def sections(d):
    assert d[:4] == b'\x7fELF' and d[4] == 1, 'not ELF32'
    shoff = struct.unpack_from('<I', d, 32)[0]; shentsize, shnum, shstrndx = struct.unpack_from('<HHH', d, 46)
    secs = []
    for i in range(shnum):
        nm, ty, fl, ad, off, sz = struct.unpack_from('<IIIIII', d, shoff + i * shentsize)
        secs.append((nm, off, sz))
    stroff = secs[shstrndx][1]
    out = {}
    for nm, off, sz in secs:
        e = d.index(b'\0', stroff + nm); out[d[stroff + nm:e].decode()] = (off, sz)
    return out
bad = 0
for ko in sys.argv[2:]:
    d = open(ko, 'rb').read(); s = sections(d)
    off, sz = s['.modinfo']; mi = d[off:off + sz].split(b'\0')
    vermagic = [x[9:].decode() for x in mi if x.startswith(b'vermagic=')][0]
    ok = True
    if rel and not vermagic.startswith(rel + ' '):
        print(f'{ko}: vermagic "{vermagic}" does not start with kernel release {rel}'); ok = False
    n = mism = 0
    if '__versions' in s:
        off, sz = s['__versions']
        for i in range(0, sz, 64):
            crc = struct.unpack_from('<I', d, off + i)[0]; name = d[off + i + 4:off + i + 64].split(b'\0')[0].decode()
            n += 1
            if name in syms and syms[name] != crc:
                print(f'{ko}: CRC mismatch {name}: module 0x{crc:08x} kernel 0x{syms[name]:08x}'); mism += 1; ok = False
            elif name not in syms:
                print(f'{ko}: symbol {name} not in Module.symvers (may be exported by another module)')
    print(f'{os.path.basename(ko)}: {"OK" if ok else "MISMATCH"} (vermagic "{vermagic}", {n} versioned symbols, {mism} crc mismatches)')
    bad += not ok
sys.exit(1 if bad else 0)
