#!/usr/bin/env python3
"""KYF37: HAL mm_camera_util_sendmsg treats status 0x20002 as success; stock daemon reports 2 (MSM_CAMERA_BUF_MAP_SUCESS). Translate in NOTIFY (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 notify status' in s:
    print('already'); raise SystemExit
NL = chr(10); T = chr(9)
anchor = T + T + T + "event_data->command = 1;" + NL
assert s.count(anchor) == 1
add = T + T + "/* KYF37 notify status */" + NL + T + T + "if (event_data->status == MSM_CAMERA_BUF_MAP_SUCESS)" + NL + T + T + T + "event_data->status = 0x20002;" + NL
s = s.replace(anchor, anchor + add)
open(p, 'w').write(s); print('patched')
