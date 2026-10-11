from pathlib import Path
import subprocess
p=Path('/home/pablo/kyf37-rom/stock-system/lib/hw/camera.msm8909.so')
s=subprocess.check_output(['readelf','-Ws',str(p)],text=True)
for line in s.splitlines():
 if 'getCameraInfo' in line or 'get_camera_info' in line:print(line)
