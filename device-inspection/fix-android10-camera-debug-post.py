#!/usr/bin/env python3
"""KYF37: debug print in msm_post_event of the event posted to the daemon (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 dbg post' in s:
    print('already'); raise SystemExit
NL = chr(10); T = chr(9); BS = chr(92)
old = T + "v4l2_event_queue(vdev, event);" + NL + NL + T + "if (timeout < 0) {"
assert s.count(old) == 1
new = (T + "/* KYF37 dbg post */" + NL + T + 'pr_info("kyf37cam: post id=%d command=%x sid=%u stream=%u arg=%x' + BS + 'n", event->id, event_data->command, event_data->session_id, event_data->stream_id, event_data->arg_value);' + NL + old)
open(p, 'w').write(s.replace(old, new)); print('patched')
