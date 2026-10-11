#!/usr/bin/env python3
"""Idempotent: UI smoothness tuning found by measurement on 2026-10-11 (tools/gpu-jank-test.sh, Settings D-pad scroll, gfxinfo jank):
  baseline 2 cores online + GPU free to drop to 200 MHz  -> ~45-58 % janky frames, p95 40-60 ms
  4 cores online (core_ctl min_cpus=4)                    -> ~28 %
  GPU devfreq min_freq 307 MHz                            -> ~30 % alone; with 4 cores ~19 %  (409 MHz gives ~14-19 %, 200 MHz + long idle_timer none)
  idle_timer had no effect.  Installs init.kyf37.uiperf.rc (applied at boot_completed). Run in WSL."""
from pathlib import Path
d = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
rc = '''# UI smoothness (fix-android10-gpu-ui-perf.py): keep all four A7 cores online and the Adreno 304 from dropping to its lowest clock
on property:sys.boot_completed=1
    write /sys/devices/system/cpu/cpu0/core_ctl/min_cpus 4
    write /sys/class/kgsl/kgsl-3d0/devfreq/min_freq 307200000
'''
f = d / 'init.kyf37.uiperf.rc'
if not f.exists() or f.read_text() != rc:
    f.write_text(rc, newline=chr(10)); print('wrote', f)
mk = d / 'device.mk'
s = mk.read_text()
line = 'PRODUCT_COPY_FILES += device/kyocera/kyf37/init.kyf37.uiperf.rc:system/etc/init/init.kyf37.uiperf.rc'
if 'init.kyf37.uiperf.rc' not in s:
    mk.write_text(s.rstrip(chr(10)) + chr(10) + line + chr(10), newline=chr(10)); print('device.mk updated')
print('done')
