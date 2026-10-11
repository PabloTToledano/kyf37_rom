from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10');p=r/'drivers/base/firmware_class.c';s=p.read_text();a=s.find('fw_path');print(s[a:a+1000])
p=Path('/home/pablo/kyf37-rom/kernel-android10-gcc48-build/.config');print('\n'.join(l for l in p.read_text().splitlines() if 'FW_LOADER' in l))
p=r/'drivers/net/wireless/wcnss/wcnss_wlan.c';lines=p.read_text().splitlines()
for i,l in enumerate(lines):
 if 'nvbin_dnld_work' in l or 'nv_dnld' in l or 'nvbin_dnld_req' in l:print(i+1,l)
