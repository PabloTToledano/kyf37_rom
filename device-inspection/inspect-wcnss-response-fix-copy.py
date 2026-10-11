from pathlib import Path
r=Path('/home/pablo/kyf37-android10');p=r/'vendor/kyocera/kyf37/kyf37-vendor.mk';s=p.read_text();s=s.replace('PRODUCT_COPY_FILES += vendor/kyocera/kyf37/proprietary/bin/wcnss_service:system/bin/wcnss_service','PRODUCT_COPY_FILES += vendor/kyocera/kyf37/proprietary/bin/wcnss_service:system/bin/wcnss_service_stock')
p.write_text(s)
s=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c').read_text()
for term in ['case WCNSS_NV_DOWNLOAD_RSP','case WCNSS_NVBIN_DNLD_RSP','case WCNSS_CBC_COMPLETE_IND','wcnss_trigger_config(struct']:
 a=s.find(term);print(term,s[a:a+2000])
