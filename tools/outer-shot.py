#!/usr/bin/env python3
"""Capture the 128x36 outer panel (fb1) to a scaled PNG: python tools/outer-shot.py out.png [scale]. Needs adb root."""
import subprocess, sys, zlib, struct
ADB = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
out = sys.argv[1]; k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
raw = subprocess.run([ADB, 'exec-out', 'dd', 'if=/dev/graphics/fb1', 'bs=9216', 'count=1'], capture_output=True).stdout[:9216]
assert len(raw) == 9216, len(raw)
W, H = 128, 36
rows = []
for y in range(H):
    line = bytearray()
    for x in range(W):
        v = raw[(y * W + x) * 2] & 0x10
        line += (b'\xff\xff\xff' if v else b'\x10\x10\x18') * k
    rows += [b'\x00' + bytes(line)] * k
def chunk(t, d): c = struct.pack('>I', len(d)) + t + d; return c + struct.pack('>I', zlib.crc32(t + d))
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W * k, H * k, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b'')
open(out, 'wb').write(png); print('wrote', out)
