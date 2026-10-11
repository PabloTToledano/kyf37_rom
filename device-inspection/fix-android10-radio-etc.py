#!/usr/bin/env python3
"""KYF37: ship stock radio config files that the Android 10 ROM lacked (idempotent, WSL):
 /system/etc/data/{qmi_config,dsi_config,netmgr_config}.xml (qmuxd/dsi_netctrl/netmgrd) and /system/etc/sec_config (irsc_util IPC-router security rules).
Sources: the owner's stock system image (~/kyf37-rom/stock-system/etc)."""
import os, shutil
home = os.path.expanduser('~')
S = home + '/kyf37-rom/stock-system/etc'
ven = home + '/kyf37-android10/vendor/kyocera/kyf37'
mk = ven + '/kyf37-vendor.mk'
s = open(mk).read()
files = [('data/' + n, 'etc/data/' + n) for n in ('qmi_config.xml', 'dsi_config.xml', 'netmgr_config.xml')] + [('sec_config', 'etc/sec_config')]
for src_rel, dst_rel in files:
    src = S + '/' + src_rel
    if not os.path.exists(src):
        print('missing in stock:', src_rel); continue
    dst = ven + '/proprietary/' + dst_rel
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    line = 'vendor/kyocera/kyf37/proprietary/' + dst_rel + ':system/' + dst_rel
    if line not in s:
        s = s.rstrip() + chr(10) + 'PRODUCT_COPY_FILES += ' + line + chr(10)
        print('added', dst_rel)
open(mk, 'w').write(s)
