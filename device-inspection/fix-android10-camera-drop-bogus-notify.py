#!/usr/bin/env python3
"""KYF37: the stock daemon sends two NOTIFYs per buffer map: a bogus one (session 0, id 0, command 0) and a
well-formed one. Accept the bogus one (return 0 so the daemon is happy) but do not deliver it: delivering it
gives the HAL a stale event in its single wait slot (race => STREAM_INFO_SYNC NACK). Idempotent."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 drop bogus' in s:
    print('already'); raise SystemExit
NL = chr(10); T = chr(9)
anchor = T + "case MSM_CAM_V4L2_IOCTL_NOTIFY: {" + NL
i = s.index(anchor, s.index("static long msm_private_ioctl"))
add = (T + T + "/* KYF37 drop bogus */" + NL + T + T + "if (!event_data->v4l2_event_id && !event_data->command) {" + NL +
       T + T + T + "rc = 0;" + NL + T + T + T + "break;" + NL + T + T + "}" + NL)
s = s[:i + len(anchor)] + add + s[i + len(anchor):]
open(p, 'w').write(s); print('patched')
