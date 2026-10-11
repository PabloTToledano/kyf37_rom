#!/usr/bin/env python3
"""rild / QCRIL fixes found by the radio agent (2026-10-08). Idempotent. Run in WSL:

    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-radio-rild.py

1. rild SIGSEGV (fault addr 0x20300868 in IInterface::asBinder(), called from libperipheral_client.so
   pm_register_connect <- pm_client_register <- qmi_ril_peripheral_mng_init) on EVERY start.
   The stock libperipheral_client.so builds Android-5 C++ Binder objects that are corrupt on Android 10.
   The same stock library is also what pm-service uses to call clients back; live test on the phone showed that
   when a client with a callback registers and votes, pm-service itself dies with SIGSEGV ("modem new state:
   going on-line" is its last log line), so replacing only the client library (libpm_client_a10) is not enough.
   Fix used here: libril-qc-qmi-1.so is repointed (DT_NEEDED) to libpmstub_kyf37.so, a tiny C library with the
   five pm_client_* functions that never touches Binder.  The MSM8909 modem is booted by the kernel (pil-q6v5-mss),
   so QCRIL does not need a real power vote.  pm-service/audio/gps keep the stock library untouched.
2. qseecomd exits with status 255 every 5 s ("dlopen(librpmb.so) failed"): librpmb.so/libssd.so/libdrmtime.so
   from the stock image were never copied into the ROM.  They are installed to /vendor/lib.

If fix-android10-pm-client.py (libpm_client_a10) was applied earlier its DT_NEEDED repoint is replaced by this one.
"""
import hashlib
import shutil
from pathlib import Path

WIN = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
TREE = Path.home() / 'kyf37-android10'
DEV = TREE / 'device/kyocera/kyf37'
VLIB = TREE / 'vendor/kyocera/kyf37/proprietary/vendor/lib'
STOCK = Path.home() / 'kyf37-rom/stock-system/vendor/lib'
KEEP = Path.home() / 'kyf37-rom/modem-fix'
STUB_SRC = WIN / 'third-party/radio/libpmstub_kyf37.so'
BLOB = VLIB / 'libril-qc-qmi-1.so'

NEW = b'libpmstub_kyf37.so\0'
OLDS = [b'libperipheral_client.so\0', b'libpm_client_a10.so\0']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --- 1. blobs ----------------------------------------------------------
VLIB.mkdir(parents=True, exist_ok=True)
shutil.copyfile(STUB_SRC, VLIB / 'libpmstub_kyf37.so')
for name in ('librpmb.so', 'libssd.so', 'libdrmtime.so'):
    shutil.copyfile(STOCK / name, VLIB / name)
    print('installed', name, sha(VLIB / name)[:12])

# --- 2. repoint QCRIL ---------------------------------------------------
KEEP.mkdir(parents=True, exist_ok=True)
data = BLOB.read_bytes()
if data.count(NEW) == 1:
    print('qcril already uses libpmstub_kyf37.so')
else:
    for old in OLDS:
        if data.count(old) == 1:
            backup = KEEP / 'libril-qc-qmi-1.so.stock'
            if not backup.exists() and old == OLDS[0]:
                backup.write_bytes(data)  # pristine stock blob; (a repointed blob never overwrites this)
            assert len(NEW) <= len(old), 'stub name longer than the slot it replaces'
            data = data.replace(old, NEW + b'\0' * (len(old) - len(NEW)), 1)
            BLOB.write_bytes(data)
            print('repointed DT_NEEDED %r -> %r' % (old[:-1].decode(), NEW[:-1].decode()))
            break
    else:
        raise SystemExit('unexpected libril-qc-qmi-1.so (no known NEEDED slot)')
print('qcril sha256', sha(BLOB))

# --- 3. device.mk -------------------------------------------------------
MARK = '# radio-agent: QCRIL peripheral stub + qseecomd libs'
mk = DEV / 'device.mk'
lines = mk.read_text().split('\n')
out = []
i = 0
while i < len(lines):
    if lines[i] == MARK:
        i += 1
        while i < len(lines) and (lines[i].startswith('PRODUCT_COPY_FILES') or lines[i].startswith('    ')):
            i += 1
        continue
    out.append(lines[i])
    i += 1
ETC = Path.home() / 'kyf37-rom/stock-system/etc'
(DEV / 'radio').mkdir(exist_ok=True)
etc_rules = []
for rel in ('data/qmi_config.xml', 'data/dsi_config.xml', 'data/netmgr_config.xml', 'sec_config'):
    dst = DEV / 'radio' / ('stock_' + rel.replace('/', '_'))
    shutil.copyfile(ETC / rel, dst)
    etc_rules.append('    device/kyocera/kyf37/radio/%s:system/etc/%s' % (dst.name, rel))
libs = ['libpmstub_kyf37.so', 'librpmb.so', 'libssd.so', 'libdrmtime.so']
rules = etc_rules + ['    vendor/kyocera/kyf37/proprietary/vendor/lib/%s:system/vendor/lib/%s' % (n, n) for n in libs]
text = '\n'.join(out).rstrip('\n') + '\n\n' + MARK + '\nPRODUCT_COPY_FILES += \\\n' + ' \\\n'.join(rules) + '\n'
mk.write_text(text)

# --- 4. blob list (documentation / extract-files) -------------------------
pf = TREE / 'vendor/kyocera/kyf37/proprietary-files.txt'
if pf.exists():
    t = pf.read_text()
    for n in ['librpmb.so', 'libssd.so', 'libdrmtime.so']:
        if 'vendor/lib/' + n not in t:
            t = t.rstrip('\n') + '\nvendor/lib/%s\n' % n
    pf.write_text(t)
print('device.mk updated')
