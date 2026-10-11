import subprocess
from pathlib import Path
r=Path('/home/pablo/kyf37-rom/wlan-prima-caf-123')
subprocess.run(['rg','-n','HAL_STATUS_SUCCESS|HAL_STATUS.*CFG|HAL_STATUS.*38|Unknown HAL status','riva','CORE/WDI'],cwd=r)
