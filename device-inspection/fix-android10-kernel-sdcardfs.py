#!/usr/bin/env python3
"""KYF37: add AOSP android-3.10 sdcardfs to the kernel tree (idempotent, WSL). See third-party/sdcardfs/README.md."""
import os, shutil
home = os.path.expanduser('~')
k = home + '/kyf37-rom/kernel-android10'
src = home + '/third-party-sdcardfs/android-3.10/fs/sdcardfs'
dst = k + '/fs/sdcardfs'
if not os.path.isdir(dst):
    shutil.copytree(src, dst)
    print('copied')
def edit(path, old, new, marker):
    s = open(path).read()
    if marker in s:
        return
    assert s.count(old) == 1, (path, s.count(old))
    open(path, 'w').write(s.replace(old, new))
    print('edited', path)
edit(k + '/fs/Kconfig', 'source "fs/ecryptfs/Kconfig"', 'source "fs/ecryptfs/Kconfig"' + chr(10) + 'source "fs/sdcardfs/Kconfig"', 'fs/sdcardfs/Kconfig')
edit(k + '/fs/Makefile', 'obj-$(CONFIG_ECRYPT_FS)', 'obj-$(CONFIG_SDCARD_FS)' + chr(9) + '+= sdcardfs/' + chr(10) + 'obj-$(CONFIG_ECRYPT_FS)', 'sdcardfs/')
cfg = k + '/arch/arm/configs/KYF37_defconfig'
s = open(cfg).read()
if 'CONFIG_SDCARD_FS=y' not in s:
    open(cfg, 'w').write(s.rstrip(chr(10)) + chr(10) + 'CONFIG_SDCARD_FS=y' + chr(10))
    print('defconfig updated')
# the gcc48 build dir keeps its own .config (copied once), so set it there too
for bc in (home + '/kyf37-rom/kernel-android10-gcc48-build/.config', home + '/kyf37-rom/kernel-android10-build/.config'):
    if os.path.exists(bc):
        t = open(bc).read()
        if 'CONFIG_SDCARD_FS=y' not in t:
            open(bc, 'w').write(t.rstrip(chr(10)) + chr(10) + 'CONFIG_SDCARD_FS=y' + chr(10))
            print('config updated', bc)
