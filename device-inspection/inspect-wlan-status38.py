from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-rom')
subprocess.run(['rg','-n','38,|= 38|=38','wlan-prima-caf-123/CORE/WDI','wlan-prima-caf-123/CORE/MAC'],cwd=r)
print('trees',*[str(p) for p in r.glob('*wlan*')],sep='\n')
