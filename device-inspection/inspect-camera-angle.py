import subprocess
from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10')
subprocess.run(['rg','-n','mount-angle|mount_angle|entity.flags',str(r/'drivers/media/platform/msm/camera_v2/sensor/msm_sensor_driver.c')])
for p in (r/'arch/arm/boot/dts').rglob('*.dtsi'):
 s=p.read_text()
 if 'ov8856' in s:
  print(p);print('\n'.join(x for x in s.splitlines() if 'mount' in x or 'ov8856' in x))
