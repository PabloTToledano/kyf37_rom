from pathlib import Path
s=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/net/wireless/wcnss/wcnss_wlan.c').read_text()
for term in ['wcnss_smd_notify','wcnss_ctrl_probe','wcnss_post_bootup','wcnss_nvbin_dnld_main','smd_named_open_on_edge']:
 a=s.find(term);print('\n',term,'\n',s[max(0,a-120):a+2300])
