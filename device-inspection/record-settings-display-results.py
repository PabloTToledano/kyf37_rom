from pathlib import Path
import hashlib,json,shutil
base=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
report={'about_page':{'device_reproduction':'Null WifiManager.getFactoryMacAddresses in About preference controller','source_build':'passed','data_apk_install':'passed','device_activity_launch':'passed','visual_proof':'device-inspection/settings-about-fixed.png','apk_sha256':hashlib.sha256((base/'device-inspection/Settings-about-fixed.apk').read_bytes()).hexdigest(),'host_regression':'blocked during Robolectric application setup: missing /system/framework/org.lineageos.platform-res.apk; five tests did not reach assertions'},'tearing':{'owner_report':'only physical display; horizontal tearing','gpu':'Qualcomm Adreno304 GLES3 hardware active','force_client_composition':'owner reported still tearing; reverted','acquire_fence_wait':'compiled and temporarily loaded; debug.hwc.kyf37_sync_wait=1; owner outcome pending','persistent_graphics_defaults_changed':False}}
(base/'device-inspection/settings-and-display-test-results.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copy2('/home/pablo/kyf37-settings-regression.log',base/'device-inspection/settings-about-host-regression.log')
print('Results and host test limitation recorded')
