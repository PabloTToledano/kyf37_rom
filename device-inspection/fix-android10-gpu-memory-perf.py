"""gpu agent: enable zram swap (v13 never did: ro.config.zram trigger does not fire for a build.prop value) and set swappiness.
Installs init.kyf37.gpu.rc through device.mk. WSL, idempotent."""
from pathlib import Path
d = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
(d/'init.kyf37.gpu.rc').write_text('''# gpu agent: memory tuning for the 1 GB device
on property:sys.boot_completed=1
    write /sys/block/zram0/disksize 402653184
    exec -- /system/bin/mkswap /dev/block/zram0
    exec -- /system/bin/swapon /dev/block/zram0
    write /proc/sys/vm/swappiness 80
''')
p = d/'device.mk'; s = p.read_text()
line = 'PRODUCT_COPY_FILES += device/kyocera/kyf37/init.kyf37.gpu.rc:system/etc/init/init.kyf37.gpu.rc'
if 'init.kyf37.gpu.rc' not in s: p.write_text(s.rstrip()+'\n'+line+'\n')
print('ok')
