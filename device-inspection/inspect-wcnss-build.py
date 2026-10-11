from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
for p in [r/'device/kyocera/kyf37/device.mk',r/'vendor/kyocera/kyf37/kyf37-vendor.mk']:
 for i,l in enumerate(p.read_text().splitlines()):
  if 'wcnss' in l:print(p,i,l)
import subprocess
subprocess.run(['rg','-n','LOCAL_MODULE.*wcnss_service|name: "wcnss_service"','hardware','vendor','device'],cwd=r)
