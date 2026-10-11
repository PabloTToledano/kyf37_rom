import subprocess
p='/home/pablo/kyf37-rom/stock-system/lib/libmmcamera_interface.so'
s=subprocess.check_output(['readelf','-Ws',p],text=True)
print('\n'.join(x for x in s.splitlines() if 'get_num_of_cameras' in x))
