from pathlib import Path
r=Path('/home/pablo/kyf37-android10');p=r/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java';s=p.read_text();a=s.find('The exterior side key');print(s[a-1300:a+1800])
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c');s=p.read_text()
for name in ['int wcnss_device_ready','int wcnss_trigger_config']:
 a=s.find(name);print(s[a:a+1100])
