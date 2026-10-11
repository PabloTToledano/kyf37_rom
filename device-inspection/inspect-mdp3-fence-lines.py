from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/mdp3_ctrl.c');s=p.read_text().splitlines()
for i,l in enumerate(s):
 if any(x in l for x in ['retire_fence','buf_sync','sync_fence_wait','MDP_BUF_SYNC','timeline']):print(i+1,l)
