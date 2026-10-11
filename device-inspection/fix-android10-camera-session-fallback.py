#!/usr/bin/env python3
"""KYF37: route msm_private_ioctl events with unknown session id to the only active camera session (idempotent)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/drivers/media/platform/msm/camera_v2/msm.c')
s = open(p).read()
if 'KYF37 session fallback' in s:
    print('already patched'); raise SystemExit
old = """		list, __msm_queue_find_session, &session_id);

	if (!session)
		return -EINVAL;

	switch (cmd) {
	case MSM_CAM_V4L2_IOCTL_NOTIFY: {"""
new = """		list, __msm_queue_find_session, &session_id);

	/* KYF37 session fallback: single-sensor device, daemon may send a
	 * session id that does not match the kernel numbering. */
	if (!session) {
		unsigned long fl;
		spin_lock_irqsave(&msm_session_q->lock, fl);
		if (!list_empty(&msm_session_q->list))
			session = list_first_entry(&msm_session_q->list,
				struct msm_session, list);
		spin_unlock_irqrestore(&msm_session_q->lock, fl);
		if (session)
			pr_info("%s: session %u routed to %u\\n", __func__,
				session_id, session->session_id);
	}

	if (!session)
		return -EINVAL;

	switch (cmd) {
	case MSM_CAM_V4L2_IOCTL_NOTIFY: {"""
assert s.count(old) == 1
open(p, 'w').write(s.replace(old, new))
print('patched')
