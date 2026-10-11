from pathlib import Path
import subprocess
root=Path('/home/pablo/kyf37-android10')
subprocess.run(['rg','-n','media_codecs|ccodec',str(root/'device/kyocera/kyf37'),str(root/'vendor/kyocera/kyf37')])
subprocess.run(['ffmpeg','-v','error','-i','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/scrcpy-omx-test.mkv','-frames:v','1','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/scrcpy-omx-frame.png'])
