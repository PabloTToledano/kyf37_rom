import subprocess
from pathlib import Path
log=Path('/home/pablo/kyf37-rom/kernel-v9-accounting-build.log')
with log.open('wb') as f:
 p=subprocess.Popen(['bash','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-android10-kernel-gcc48.sh'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
print('Kernel build PID',p.pid,'log',log)
