from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/mdp3_dma.c');s=p.read_text()
for needle in ['static int mdp3_dma_update','mdp3_dma_update(']:
 a=s.find(needle);print(s[a:a+4300])
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/mdss_fb.c');lines=p.read_text().splitlines()
for i,l in enumerate(lines):
 if 'mdss_fb_wait_for_fence(' in l:print(i+1,'\n'.join(lines[max(0,i-3):i+5]))
