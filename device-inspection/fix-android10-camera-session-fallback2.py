#!/usr/bin/env python3
"""KYF37: also rewrite event_data->session_id to the routed session so the HAL accepts the event (idempotent, run after fix-android10-camera-session-fallback.py)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 rewrite sid' in s:
    print('already patched'); raise SystemExit
old = "\t\tif (session)\n\t\t\tpr_info("
new = "\t\tif (session) {\n\t\t\t/* KYF37 rewrite sid */\n\t\t\tevent_data->session_id = session->session_id;\n\t\t\tsession_id = session->session_id;\n\t\t}\n\t\tif (session)\n\t\t\tpr_info("
assert s.count(old) == 1
open(p, 'w').write(s.replace(old, new)); print('patched')
