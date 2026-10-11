from pathlib import Path
import subprocess
p='/home/pablo/kyf37-rom/stock-system/lib/libmmcamera_interface.so'
obj='/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-objdump'
print(subprocess.check_output([obj,'-d','-C','--start-address=0x3a58','--stop-address=0x3a70',p],text=True))
