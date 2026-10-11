#!/usr/bin/env python3
"""KYF37: strip the temporary kyf37cam/routed debug prints from camera_v2/msm.c (idempotent)."""
import os, re
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
out = []
lines = s.split(chr(10))
i = 0
n = 0
while i < len(lines):
    l = lines[i]
    if 'KYF37 dbg' in l:            # comment line (dbg, dbg2, dbg post)
        i += 1; n += 1; continue
    if 'kyf37cam:' in l:            # the pr_info statement (single physical line in our patches)
        i += 1; n += 1; continue
    if 'pr_info("%s: session %u routed to %u' in l:
        # statement spans two lines: this one and the next (args)
        i += 2; n += 1
        # remove the now-pointless 'if (session)' that guarded it
        if out and out[-1].strip() == 'if (session)':
            out.pop()
        continue
    out.append(l); i += 1
open(p, 'w').write(chr(10).join(out))
print('removed', n)
