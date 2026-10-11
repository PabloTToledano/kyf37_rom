from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/native/libs/input/KeyLayoutMap.cpp');s=p.read_text();a=s.find('Parser::parseKey');print(s[a:a+3200])
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c');s=p.read_text()
for l in s.splitlines():
 if 'NVBIN_FILE' in l or ('nvbin_dnld_req' in l and 'work' in l):print(l)
