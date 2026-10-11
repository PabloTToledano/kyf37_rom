from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/mdss_fb.c');s=p.read_text().splitlines()
for i,l in enumerate(s):
 if 'retire_fen' in l or 'MDP_BUF_SYNC_FLAG' in l or ('threshold' in l and 'sync' in l):print(i+1,'\n'.join(s[max(0,i-2):i+5]))
p=Path('/home/pablo/kyf37-android10/hardware/qcom-caf/msm8916/display/libhwcomposer/hwc_utils.cpp');s=p.read_text();a=s.index('//Accumulate acquireFenceFds');print(s[a:a+6000])
