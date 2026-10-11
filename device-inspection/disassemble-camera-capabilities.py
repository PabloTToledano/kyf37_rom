import subprocess
p='/home/pablo/kyf37-rom/stock-system/lib/hw/camera.msm8909.so'
obj='/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-objdump'
s=subprocess.check_output([obj,'-d','-C','--start-address=0x440d0','--stop-address=0x44300',p],text=True)
print(s)
