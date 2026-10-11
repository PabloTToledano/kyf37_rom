from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-android10');k=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss')
for p in (r/'hardware/qcom-caf/msm8916/display').rglob('*.cpp'):
 lines=p.read_text().splitlines()
 for i,l in enumerate(lines):
  if 'wait_for_finish' in l or 'MDP_DISPLAY_COMMIT' in l: print(p.name,i+1,'\n'.join(lines[max(0,i-2):i+5]))
print(subprocess.run(['pgrep','-af','ninja|javac|java'],capture_output=True,text=True).stdout[-2800:])
