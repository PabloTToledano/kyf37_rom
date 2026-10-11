#!/usr/bin/env python3
"""KYF37: debug print of NOTIFY event fields in msm_private_ioctl (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 dbg' in s:
    print('already'); raise SystemExit
old = "\tswitch (cmd) {\n\tcase MSM_CAM_V4L2_IOCTL_NOTIFY: {\n\t\tif (WARN_ON(!session->event_q.vdev)) {"
new = "\t/* KYF37 dbg */\n\tpr_info(\"kyf37cam: cmd=%x type=%x id=%x command=%u status=%u sid=%u stream=%u\n\", cmd, event_data->v4l2_event_type, event_data->v4l2_event_id, event_data->command, event_data->status, event_data->session_id, event_data->stream_id);\n" + old
assert s.count(old) == 1
new = new.replace('\x5c', chr(92)); open(p, 'w').write(s.replace(old, new)); print('patched')
