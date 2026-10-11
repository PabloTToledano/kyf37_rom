from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/mdp3_dma.c');lines=p.read_text().splitlines()
for i,l in enumerate(lines):
 if 'update' in l and ('static' in l or 'int ' in l):print(i+1,'\n'.join(lines[i:i+80]))
