from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
for f in ['hardware/qcom-caf/wlan/wcnss-service/Android.mk','hardware/qcom-caf/wlan/wcnss-service/wcnss_service.c']:
 p=r/f
 if p.suffix=='.mk':print(p.read_text())
 else:
  s=p.read_text()
  for x in ['main(','/dev/wcnss','wcnss_read_and_store_cal_data']:
   a=s.find(x);print(s[a:a+1000])
s=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c').read_text()
for x in ['CBC_COMPLETE','WCNSS_CBC','NV_DOWNLOAD_RSP','no space available for smd frame']:
 a=s.find(x);print(x,s[max(0,a-500):a+1400])
