#!/usr/bin/env python3
"""Host verification of the signed keitai recovery image (no phone needed).
Checks header geometry, owner-key signature incl. the '/recovery' attribute, kernel+dt identical to the
working shipped TWRP, ramdisk contents (adbd, twrp CLI, recovery, keitai theme), no host-test hooks, size."""
import gzip, hashlib, struct, sys, runpy
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

p = Path(__file__).resolve().parent
dev = p.parent / 'kyf37-twrp-device'
kd = dev / 'keitai'
t = runpy.run_path(str(p / 'prepare-recovery-signing.py'))
read_tlv, children, boot_parts = t['read_tlv'], t['children'], t['boot_parts']
TARGET = b'/boot' if '--boot' in sys.argv else b'/recovery'
args = [a for a in sys.argv[1:] if a != '--boot']
img = Path(args[0]) if args else kd / ('kyf37-keitai-recovery-BOOTSLOT-owner-signed.img' if TARGET == b'/boot' else 'kyf37-keitai-recovery-owner-signed.img')
ref = dev / 'kyf37-twrp-owner-signed.img'
fails = []


def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c:
        fails.append(m)


def parts(b):
    f = struct.unpack_from('<10I', b, 8)
    page = f[7]
    al = lambda n: (n + page - 1) // page * page
    k = page
    r = k + al(f[0])
    s = r + al(f[2])
    d = s + al(f[4])
    return f, b[k:k + f[0]], b[r:r + f[2]], b[d:d + f[8]]


b = img.read_bytes()
rb = ref.read_bytes()
ok(len(b) == 16777216, 'image is exactly 16 MiB (recovery partition size)')
f, kern, rd, dt = parts(b)
rf, rkern, rrd, rdt = parts(rb)
ok(b[:8] == b'ANDROID!', 'ANDROID! magic')
ok(f[1] == rf[1] and f[3] == rf[3] and f[5] == rf[5] and f[6] == rf[6] and f[7] == 2048, 'load addresses/page size identical to working TWRP')
ok(b[64:64 + 512] == rb[64:64 + 512], 'cmdline identical to working TWRP')
ok(kern == rkern, 'kernel byte-identical to working TWRP (%d bytes)' % len(kern))
ok(dt == rdt, 'device tree section byte-identical (%d bytes)' % len(dt))
bb, ff, end = boot_parts(img)
_, payload, _, _ = read_tlv(bb, end)
sg = children(payload)
attr = children(sg[-2][1])
ok(attr[0][1] == TARGET and int.from_bytes(attr[1][1], 'big') == end, 'signed attribute is %s with image end %d' % (TARGET.decode(), end))
der = (dev / 'owner-public-key.der').read_bytes()
n_e = children(read_tlv(der)[1])
pub = rsa.RSAPublicNumbers(int.from_bytes(n_e[1][1], 'big'), int.from_bytes(n_e[0][1], 'big')).public_key()
try:
    pub.verify(sg[-1][1], bb[:end] + sg[-2][2], padding.PKCS1v15(), hashes.SHA256())
    sig_ok = True
except Exception:
    sig_ok = False
ok(sig_ok, 'RSA-2048/SHA-256 signature verifies with the owner public key')
tmpl = boot_parts(p.parent / 'phone-backup/kyf37-root-backup' / (TARGET[1:].decode() + '.img'))
_, tpay, _, _ = read_tlv(tmpl[0], tmpl[2])
tsg = children(tpay)
ok([c[2] for c in sg[:3]] == [c[2] for c in tsg[:3]], 'signature envelope header fields equal the vendor recovery envelope')
ok(len(b[end:].rstrip(b'\0')) > 0 and len(b) - end - len(b[end:].rstrip(b'\0')) > 0, 'envelope followed by zero padding')
raw = gzip.decompress(rd)
files = {}
pos = 0
while True:
    assert raw[pos:pos + 6] == b'070701', 'cpio magic'
    h = [int(raw[pos + 6 + 8 * i:pos + 14 + 8 * i], 16) for i in range(13)]
    fsize, nlen = h[6], h[11]
    name = raw[pos + 110:pos + 110 + nlen - 1].decode()
    pos = (pos + 110 + nlen + 3) & ~3
    data = raw[pos:pos + fsize]
    pos = (pos + fsize + 3) & ~3
    if name == 'TRAILER!!!':
        break
    files[name] = data
for need in ('sbin/recovery', 'sbin/adbd', 'sbin/twrp', 'sbin/busybox', 'twres/ui.xml', 'twres/splash.xml', 'etc/recovery.fstab',
             'init.recovery.qcom.rc', 'init.rc'):
    ok(need in files, 'ramdisk has ' + need)
ok(b'keymenu' in files['twres/ui.xml'], 'ramdisk theme is the keitai theme')
stale = [n for n in files if n.startswith('twres/images/') and n.endswith('.png') and n not in ('twres/images/progress_empty.png', 'twres/images/progress_fill.png')]
ok(not stale, 'no stale stock-theme images (%d)' % len(stale))
ok(b'fb.raw' not in files['sbin/recovery'], 'recovery binary has no host-test framebuffer hook')
ok(all(b'ashmem-XXXXXX' not in d for n, d in files.items() if n.endswith('libcutils.so')), 'libcutils has no host-test ashmem hook')
ok(any(b'adbd' in d for n, d in files.items() if n.startswith('init') and n.endswith('.rc')), 'adbd started by an init rc')
ok(b'setprop service.adb.root 1' in files['init.recovery.qcom.rc'], 'root adb (service.adb.root=1) set in init.recovery.qcom.rc, independent of the GUI')
ok(b'/dev/block/bootdevice/by-name/persist' in files['etc/recovery.fstab'], 'fstab unchanged vs stock-theme build (persist listed, never offered in UI)')
print('sha256', hashlib.sha256(b).hexdigest())
print('RESULT', 'ALL PASS' if not fails else '%d FAIL' % len(fails))
sys.exit(1 if fails else 0)
