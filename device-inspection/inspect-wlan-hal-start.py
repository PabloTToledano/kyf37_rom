from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-rom')
subprocess.run(['rg','-n','HAL.*STATUS|UNKNOWN|START.*FAIL','wlan-prima-caf-123/CORE/WDI/CP/inc/wlan_hal_msg.h'],cwd=r)
print(list((r/'kernel-android10/drivers/staging').glob('*prima*')))
print((r/'wlan-prima-caf-123/CORE/WDI/CP/inc/wlan_hal_msg.h').exists())
subprocess.run(['rg','-n','HAL_START|START.*STATUS|NV_VERSION|CFG.*FAIL','wlan-prima-caf-123/CORE/WDI/CP/inc'],cwd=r)
