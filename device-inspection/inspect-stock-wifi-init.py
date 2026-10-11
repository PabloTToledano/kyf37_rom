from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-rom')
subprocess.run(['rg','-n','WCNSS_qcom_wlan_nv|WCNSS_SERVICE|wcnss','stock-system/etc/init.qcom.post_boot.sh','stock-system/etc/init.qcom.wifi.sh'],cwd=r)
subprocess.run(['rg','-n','WLAN_HAL_SUCCESS|HAL.*ERROR|INVALID.*CFG','wlan-prima-caf-123/CORE'],cwd=r,stdout=open('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/wlan-hal-errors.txt','w'))
print('headers',*[str(p) for p in (r/'wlan-prima-caf-123').rglob('*hal*msg*')],sep='\n')
