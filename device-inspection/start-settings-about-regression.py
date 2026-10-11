from pathlib import Path
import subprocess
base=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection')
s=(base/'build-kyf37-android10.sh').read_text().replace('m -j8 bootimage systemimage','export ROBOTEST_FILTER=WifiMacAddressPreferenceControllerTest\nexport ROBOTEST_FAILURE_FATAL=true\nm -j8 RunSettingsLibRoboTests')
p=base/'run-settings-about-regression.sh';p.write_bytes(s.encode())
with Path('/home/pablo/kyf37-settings-regression.log').open('wb') as log:
 proc=subprocess.Popen(['bash',str(p)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print('Regression runner PID',proc.pid)
