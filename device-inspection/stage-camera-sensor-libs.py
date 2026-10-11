from pathlib import Path
import shutil,subprocess
src=Path('/home/pablo/kyf37-rom/stock-system/vendor/lib')
out=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/camera-sensor-libs')
out.mkdir(exist_ok=True)
files=sorted(src.glob('*ov8856*'))
for p in files:
 shutil.copy2(p,out/p.name)
 if p.name=='libmmcamera_ov8856.so':
  txt=subprocess.check_output(['strings',str(p)],text=True)
  print('\n'.join(x for x in txt.splitlines() if any(w in x for w in ['sunny','actuator','dw97','bu64','rohm'])))
print('Staged',len(files),'exact original sensor/tuning libraries')
