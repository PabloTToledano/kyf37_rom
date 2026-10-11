from pathlib import Path
import subprocess
p='/home/pablo/kyf37-rom/stock-system/lib/libmmcamera_interface.so'
obj='/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-objdump'
s=subprocess.check_output([obj,'-d','-C','--start-address=0x3730','--stop-address=0x3a58',p],text=True)
Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/camera-count-disassembly.txt').write_text(s)
print(s[-6500:])
