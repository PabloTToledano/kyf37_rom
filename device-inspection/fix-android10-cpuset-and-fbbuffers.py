"""Populate cpuset groups (Android 10 expects the device to) and triple-buffer the client target. WSL; idempotent."""
from pathlib import Path
d = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
(d/'init.kyf37.perf.rc').write_text('''# Android 10 task profiles need CPUs in every cpuset group; the OEM ramdisk predates this.
on init
    write /dev/cpuset/top-app/cpus 0-3
    write /dev/cpuset/foreground/cpus 0-3
    write /dev/cpuset/system-background/cpus 0-3
    write /dev/cpuset/background/cpus 0-1
    write /dev/cpuset/restricted/cpus 0-1
''')
p = d/'device.mk'; s = p.read_text()
line = 'PRODUCT_COPY_FILES += device/kyocera/kyf37/init.kyf37.perf.rc:system/etc/init/init.kyf37.perf.rc'
if 'init.kyf37.perf.rc' not in s: p.write_text(s.rstrip()+'\n'+line+'\n')
b = d/'BoardConfig.mk'; t = b.read_text()
if 'NUM_FRAMEBUFFER_SURFACE_BUFFERS' not in t:
    b.write_text(t.rstrip()+'\n# Triple-buffer the client target so the MDP3 scanout never shares a buffer with the GPU\nNUM_FRAMEBUFFER_SURFACE_BUFFERS := 3\n')
print('ok')
# The effective knob in Android 10 is the sysprop, not the board variable.
s = p.read_text()
prop = 'PRODUCT_PROPERTY_OVERRIDES += ro.surface_flinger.max_frame_buffer_acquired_buffers=3'
if prop not in s: p.write_text(s.rstrip()+'\n'+prop+'\n')
print('prop ok')
