#!/usr/bin/env python3
"""KYF37 GPS: gps.default.so (stock Qualcomm GNSS HAL glue) calls pm_client_register() from Android-5 libperipheral_client.so;
that library cannot talk to Android 10's Binder, so loc_init fails ('PerMgrLib: modem get service fail / GPS failed to register for modem /
loc_init: pm_client_register returned -1') and the GNSS HAL never starts the location engine. Same defect and same cure as QCRIL (see
RADIO.md section 3 and fix-android10-radio-rild.py): repoint DT_NEEDED to libpmstub_kyf37.so (no-Binder C stub, third-party/radio/).
Idempotent; WSL. Also used standalone on a file: fix-android10-gps-pmstub.py --file in out"""
import sys, shutil, os
from pathlib import Path
OLD = b'libperipheral_client.so\0'
NEW = b'libpmstub_kyf37.so\0'
def patch(data):
    i = data.find(OLD)
    if i < 0:
        return None
    return data[:i] + NEW + b'\0' * (len(OLD) - len(NEW)) + data[i + len(OLD):]
if len(sys.argv) == 4 and sys.argv[1] == '--file':
    d = Path(sys.argv[2]).read_bytes()
    if NEW in d:
        print('already patched'); Path(sys.argv[3]).write_bytes(d); sys.exit(0)
    p = patch(d)
    assert p, 'NEEDED libperipheral_client.so not found'
    assert d.count(OLD) == 1, 'unexpected multiple occurrences'
    Path(sys.argv[3]).write_bytes(p); print('repointed'); sys.exit(0)
home = Path.home()
ven = home / 'kyf37-android10/vendor/kyocera/kyf37'
src = ven / 'proprietary/lib/hw/gps.default.so'
stub = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/third-party/radio/libpmstub_kyf37.so')
d = src.read_bytes()
if NEW in d:
    print('gps.default.so already uses libpmstub_kyf37.so')
else:
    orig = src.with_name('gps.default.so.stock')
    if not orig.exists():
        shutil.copyfile(src, orig)
    p = patch(d)
    assert p and d.count(OLD) == 1
    src.write_bytes(p); print('repointed gps.default.so')
# the stub lib itself is installed by fix-android10-radio-rild.py (system/vendor/lib); make sure it is in the vendor tree + copy list
dst = ven / 'proprietary/vendor/lib/libpmstub_kyf37.so'
dst.parent.mkdir(parents=True, exist_ok=True)
if not dst.exists():
    shutil.copyfile(stub, dst)
mk = ven / 'kyf37-vendor.mk'
t = mk.read_text()
line = 'vendor/kyocera/kyf37/proprietary/vendor/lib/libpmstub_kyf37.so:system/vendor/lib/libpmstub_kyf37.so'
if line not in t and 'libpmstub_kyf37.so' not in t:
    mk.write_text(t.rstrip(chr(10)) + chr(10) + 'PRODUCT_COPY_FILES += ' + line + chr(10)); print('copy rule added')
