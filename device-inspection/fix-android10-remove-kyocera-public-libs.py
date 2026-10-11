#!/usr/bin/env python3
"""Idempotent: drop public.libraries-kyocera.txt from the image. Android 10 libnativeloader aborts zygote
('Library name "libDtv.so" does not end with the company name: kyocera'), so no system_server and a boot that never
completes. The One Seg TV libs are not in this image's public list (TV.md). Run in WSL after the TV staging."""
import pathlib
dev = pathlib.Path.home() / 'kyf37-android10/device/kyocera/kyf37'
for name in ('tv-oem.mk',):
    p = dev / name
    if p.exists():
        lines = p.read_text().splitlines(True)
        keep = [l for l in lines if 'public.libraries-kyocera.txt' not in l]
        if len(keep) != len(lines):
            p.write_text(''.join(keep)); print('removed copy rule from', name)
f = dev / 'public.libraries-kyocera.txt'
if f.exists():
    f.unlink(); print('removed', f.name)
print('done')
