from pathlib import Path
p=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/ramdisk/init.kc.common.rc')
s=p.read_text().replace('setprop debug.sf.nobootanimation 0','setprop debug.sf.nobootanimation 1')
p.write_text(s)
print('Preserved charger-only disable flag; normal Android boot animation is enabled by default')
