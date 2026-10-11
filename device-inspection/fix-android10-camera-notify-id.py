#!/usr/bin/env python3
"""KYF37: stock daemon sends NOTIFY events with v4l2_event_id 0; map to a tunable id (default MSM_CAMERA_MSM_NOTIFY) (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 notify id' in s:
    print('already'); raise SystemExit
old = "static long msm_private_ioctl(struct file *file, void *fh,"
new = "/* KYF37 notify id */\nstatic int kyf37_notify_id = 7;\nmodule_param(kyf37_notify_id, int, 0644);\n\n" + old
assert s.count(old) == 1
s = s.replace(old, new)
NL = chr(10); T = chr(9)
anchor = "case MSM_CAM_V4L2_IOCTL_NOTIFY: {"
i = s.index(anchor, s.index("static long msm_private_ioctl"))
old2 = T + T + "event.id = event_data->v4l2_event_id;" + NL
j = s.index(old2, i) + len(old2)
s = s[:j] + T + T + "if (!event.id)" + NL + T + T + T + "event.id = kyf37_notify_id;" + NL + s[j:]
open(p, 'w').write(s); print('patched')
