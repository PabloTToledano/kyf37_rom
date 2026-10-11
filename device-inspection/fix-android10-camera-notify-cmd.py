#!/usr/bin/env python3
"""KYF37: stock daemon sends NOTIFY events with command 0; the HAL dispatcher only accepts command 1 (CAM_EVENT_TYPE_MAP_UNMAP_DONE) with id MSM_CAMERA_MSM_NOTIFY. Fill it in (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 notify cmd' in s:
    print('already'); raise SystemExit
NL = chr(10); T = chr(9)
anchor = T + T + "if (!event.id)" + NL + T + T + T + "event.id = kyf37_notify_id;" + NL
assert s.count(anchor) == 1
add = T + T + "/* KYF37 notify cmd */" + NL + T + T + "if (!event_data->command)" + NL + T + T + T + "event_data->command = 1;" + NL
s = s.replace(anchor, anchor + add)
open(p, 'w').write(s); print('patched')
