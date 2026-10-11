from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10')
for p in r.glob('drivers/video/msm/**/mdp3_ctrl.c'):
 lines=p.read_text().splitlines()
 for i,l in enumerate(lines):
  if any(t in l for t in ['BUF_SYNC_FLAG_RETIRE','MSMFB_BUFFER_SYNC','buf_sync->flags','retire_fen']):print(p,i+1,'\n'.join(lines[max(0,i-3):i+8]))
p=Path('/home/pablo/kyf37-android10/frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp');s=p.read_text();a=s.index('case 1008');print(s[a:a+900])
