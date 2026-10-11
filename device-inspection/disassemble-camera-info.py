import subprocess
p='/home/pablo/kyf37-rom/stock-system/lib/hw/camera.msm8909.so'
s=subprocess.check_output(['readelf','-Ws',p],text=True)
for line in s.splitlines():
 if 'getCameraInfo' in line or 'getCamInfo' in line:print(line)
obj='/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-objdump'
print(subprocess.check_output([obj,'-d','-C','--start-address=0x43a04','--stop-address=0x43a40',p],text=True))
