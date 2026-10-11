#!/usr/bin/env python3
"""Convert 480x854 RGBX raw frames written by the host-test fake framebuffer to PNG (+ optional contact sheet)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def conv(p):
    d = Path(p).read_bytes()
    im = Image.frombuffer('RGBA', (480, 854), d[:480 * 854 * 4], 'raw', 'RGBA', 0, 1).convert('RGB')
    out = Path(p).with_suffix('.png')
    im.save(out)
    return im, out

if __name__ == '__main__':
    args = sys.argv[1:]
    sheet = None
    if args and args[0] == '--sheet':
        sheet = args[1]
        args = args[2:]
    ims = []
    for a in args:
        im, out = conv(a)
        ims.append((Path(a).stem, im))
    if sheet and ims:
        cols = 4
        cw, ch = 240 + 8, 427 + 28
        rows = (len(ims) + cols - 1) // cols
        S = Image.new('RGB', (cols * cw + 8, rows * ch + 8), '#222222')
        d = ImageDraw.Draw(S)
        for i, (n, im) in enumerate(ims):
            x, y = 8 + (i % cols) * cw, 8 + (i // cols) * ch
            S.paste(im.resize((240, 427)), (x, y + 20))
            d.text((x, y + 2), n, fill='#ffffff')
        S.save(sheet)
