#!/usr/bin/env python3
"""Generate outer-v2/outerfont.bin: hinted 1-bit bitmap fonts for the 128x36 outer panel (Pillow mono rendering).
Fonts (DejaVu: free licence; Roboto Condensed: Apache 2.0) live in outer-v2/fontwork. Format (little endian):
 'PXF1', nfonts u8; per font: id u8, height u8 (cap/digit height), nglyph u16; per glyph: cp u16, adv u8, w u8, h u8, xoff s8, yoff s8
 (top row relative to baseline, negative = above), bitmap rows MSB-first, ceil(w*h/8) bytes."""
import struct, pathlib
from PIL import Image, ImageDraw, ImageFont
D = pathlib.Path(__file__).resolve().parent / 'outer-v2'
FW = D / 'fontwork'
FONTS = [  # id, file, size
    (0, 'DejaVuSans-Bold.ttf', 26), (1, 'DejaVuSans-Bold.ttf', 21), (2, 'DejaVuSans-Bold.ttf', 17),
    (3, 'DejaVuSans.ttf', 9), (4, 'DejaVuSans-Bold.ttf', 9),
    (5, 'RobotoCondensed-Bold.ttf', 15), (6, 'RobotoCondensed-Bold.ttf', 16), (7, 'DejaVuSans.ttf', 10),
]
CHARS = [chr(c) for c in list(range(32, 127)) + list(range(160, 256))]
out = bytearray(b'PXF1' + bytes([len(FONTS)]))
for fid, name, size in FONTS:
    font = ImageFont.truetype(str(FW / name), size)
    glyphs = []
    zero = Image.new('1', (64, 64)); dz = ImageDraw.Draw(zero); dz.fontmode = '1'; dz.text((16, 48), '0', font=font, fill=1, anchor='ls')
    zb = zero.getbbox(); height = zb[3] - zb[1]
    for ch in CHARS:
        img = Image.new('1', (64, 64)); d = ImageDraw.Draw(img); d.fontmode = '1'
        d.text((16, 48), ch, font=font, fill=1, anchor='ls')
        adv = max(1, round(font.getlength(ch)))
        b = img.getbbox()
        if b is None:
            glyphs.append((ord(ch), adv, 0, 0, 0, 0, b'')); continue
        w, h = b[2] - b[0], b[3] - b[1]
        px = img.crop(b).load()
        bits = bytearray((w * h + 7) // 8)
        for y in range(h):
            for x in range(w):
                if px[x, y]: i = y * w + x; bits[i // 8] |= 1 << (7 - i % 8)
        glyphs.append((ord(ch), adv, w, h, b[0] - 16, b[1] - 48, bytes(bits)))
    out += struct.pack('<BBH', fid, height, len(glyphs))
    for cp, adv, w, h, xo, yo, bits in glyphs:
        out += struct.pack('<HBBBbb', cp, adv, w, h, xo, yo) + bits
(D / 'outerfont.bin').write_bytes(bytes(out))
print('wrote outerfont.bin', len(out), 'bytes')
