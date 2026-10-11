from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-rom/stock-system')
p=next(r.rglob('libmmcamera_interface.so'))
s=subprocess.check_output(['readelf','-Ws',str(p)],text=True)
print(p);print('\n'.join(x for x in s.splitlines() if 'get_cam_info' in x))
subprocess.run(['rg','-n','get_cam_info','/home/pablo/kyf37-android10/device/kyocera/kyf37'])
