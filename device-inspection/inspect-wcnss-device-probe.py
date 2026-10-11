from pathlib import Path
s=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c').read_text()
for x in ['wcnss_wlan_probe','smd_channel_ready =','wcnss_ctrl_driver','WCNSS_CBC']:
 start=0
 while (a:=s.find(x,start))>=0:
  print(s[max(0,a-120):a+500]);start=a+len(x)
