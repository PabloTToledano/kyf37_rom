#!/usr/bin/env python3
"""KYF37: debug print of subscribed v4l2 event type/id (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 dbg2' in s:
    print('already'); raise SystemExit
old = "\treturn v4l2_event_subscribe(fh, sub, 5, NULL);"
new = "\t/* KYF37 dbg2 */\n\tpr_info(\"kyf37cam: subscribe type=%x id=%x flags=%x\" \"\x5cn\", sub->type, sub->id, sub->flags);\n" + old
assert s.count(old) == 1
new = new.replace('\x5c', chr(92))
open(p, 'w').write(s.replace(old, new)); print('patched')
