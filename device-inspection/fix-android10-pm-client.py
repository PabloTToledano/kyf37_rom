#!/usr/bin/env python3
"""Idempotent: give QCRIL an Android 10 peripheral-manager client.

Run in WSL:  python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-pm-client.py

What it does (see modem-investigation/REPORT-MODEM-LTE.md):
 1. installs device/kyocera/kyf37/pm_client/{pm_client.cpp,Android.bp}
    -> core module libpm_client_a10 (installs to /system/lib, talks /dev/binder)
 2. adds libpm_client_a10 to PRODUCT_PACKAGES in device.mk
 3. repoints ONLY libril-qc-qmi-1.so's DT_NEEDED entry from the stock
    libperipheral_client.so (Android 5 C++ objects, crashes rild in
    IInterface::asBinder) to libpm_client_a10.so.  pm-service, gps and audio
    keep the stock library untouched.  The original blob is kept next to the
    modem-fix notes with its sha256 so the change is reversible.
"""
from pathlib import Path
import hashlib
import shutil

WIN = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
TREE = Path.home() / 'kyf37-android10'
SRC = WIN / 'modem-investigation/fix/pm_client.cpp'
DEV = TREE / 'device/kyocera/kyf37'
BLOB = TREE / 'vendor/kyocera/kyf37/proprietary/vendor/lib/libril-qc-qmi-1.so'
KEEP = Path.home() / 'kyf37-rom/modem-fix'

OLD = b'libperipheral_client.so\0'
NEW = b'libpm_client_a10.so\0'

BP = '''cc_library_shared {
    name: "libpm_client_a10",
    srcs: ["pm_client.cpp"],
    shared_libs: [
        "libbinder",
        "libutils",
        "liblog",
    ],
    cflags: [
        "-Wall",
        "-Werror",
        "-fvisibility=hidden",
    ],
}
'''


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# 1. module ------------------------------------------------------------
d = DEV / 'pm_client'
d.mkdir(exist_ok=True)
shutil.copyfile(SRC, d / 'pm_client.cpp')
(d / 'Android.bp').write_text(BP)

# 2. product package ----------------------------------------------------
mk = DEV / 'device.mk'
text = mk.read_text()
line = 'PRODUCT_PACKAGES += libpm_client_a10\n'
if line not in text:
    mk.write_text(text.rstrip('\n') + '\n\n# Android 10 peripheral-manager client for QCRIL (replaces stock libperipheral_client for rild).\n' + line)

# 3. DT_NEEDED repoint ---------------------------------------------------
KEEP.mkdir(parents=True, exist_ok=True)
data = BLOB.read_bytes()
if data.count(OLD) == 1:
    backup = KEEP / 'libril-qc-qmi-1.so.stock'
    if not backup.exists():
        backup.write_bytes(data)
    new = data.replace(OLD, NEW + b'\0' * (len(OLD) - len(NEW)), 1)
    assert len(new) == len(data)
    BLOB.write_bytes(new)
    print('patched DT_NEEDED; stock sha256', hashlib.sha256(data).hexdigest())
else:
    assert data.count(NEW) == 1, 'unexpected qcril blob'
    print('qcril already repointed')
print('qcril sha256', sha(BLOB))
