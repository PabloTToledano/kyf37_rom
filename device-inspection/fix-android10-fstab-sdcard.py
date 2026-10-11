#!/usr/bin/env python3
"""KYF37: Android 10 vold matches the fstab device path with fnmatch (Lollipop used a prefix match), so the SD slot entry
'/devices/soc.0/7864900.sdhci/mmc_host' never matched -> no public volume -> camera apps said 'Insert an SD card'. Add the glob. Idempotent (WSL)."""
import os, glob
base = os.path.expanduser('~/kyf37-android10/device/kyocera/kyf37')
for f in glob.glob(base + '/ramdisk/fstab.qcom') + glob.glob(base + '/ramdisk/*/fstab.qcom'):
    s = open(f).read()
    if '7864900.sdhci/mmc_host*' in s:
        print('already', f); continue
    assert '7864900.sdhci/mmc_host ' in s, f
    open(f, 'w').write(s.replace('7864900.sdhci/mmc_host ', '7864900.sdhci/mmc_host* '))
    print('patched', f)
