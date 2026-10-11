#!/usr/bin/env python3
"""Idempotent: drop the One Seg TV apps from the image. v18 shipped FsDtvApp (jp.co.fsi.fs1seg), which crash-loops with
UnsatisfiedLinkError 'libskia.so not found' (47 crashes in one boot) and takes the screen, making the phone unresponsive.
Re-enable only after the TV stack (libskia/dtvserver) is ported; see TV.md."""
import pathlib
dev = pathlib.Path.home() / 'kyf37-android10/device/kyocera/kyf37'
changed = 0
for mk in dev.glob('*.mk'):
    lines = mk.read_text().splitlines(True)
    out = []
    for l in lines:
        if l.lstrip().startswith('PRODUCT_PACKAGES') and ('FsDtvApp' in l or 'Kyf37Tv' in l):
            parts = [p for p in l.split() if p not in ('FsDtvApp', 'Kyf37Tv')]
            if len(parts) > 2:
                out.append(' '.join(parts) + '\n')
            changed += 1
            continue
        out.append(l)
    if out != lines:
        mk.write_text(''.join(out)); print('patched', mk.name)
print('done, changed lines:', changed)
