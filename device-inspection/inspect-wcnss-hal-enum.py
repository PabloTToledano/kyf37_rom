from pathlib import Path
r=Path('/home/pablo/kyf37-rom');p=r/'wlan-prima-caf-123/riva/inc/wlan_hal_msg.h';s=p.read_text()
for term in ['WLAN_HAL_SUCCESS','WLAN_HAL_START_RSP']:
 a=s.find(term);print(s[max(0,a-150):a+3200])
p=r/'stock-system/etc/init.qcom.wifi.sh';s=p.read_text();print(s[s.find('trigger_wcnss()'):s.find('trigger_wcnss()')+1500]);print('\n'.join(s.splitlines()[270:330]))
