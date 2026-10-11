#!/usr/bin/env python3
"""Sign the keitai recovery image with the owner key (same envelope as sign-owner-recovery.py).
The private key is only loaded in memory; it is never printed or copied.
usage: sign-keitai-recovery.py [--target recovery|boot] [unsigned.img [signed.img]]
--target boot signs the SAME image with the '/boot' attribute (boot-slot test image)."""
from pathlib import Path
import hashlib, json, runpy, sys
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

p = Path(__file__).resolve().parent
dev = p.parent / 'kyf37-twrp-device'
kd = dev / 'keitai'
t = runpy.run_path(str(p / 'prepare-recovery-signing.py'))
read_tlv, children, boot_parts = t['read_tlv'], t['children'], t['boot_parts']


def tlv(tag, data):
    n = len(data)
    length = bytes([n]) if n < 128 else bytes([128 + (n.bit_length() + 7) // 8]) + n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return bytes([tag]) + length + data


def seq(*d):
    return tlv(0x30, b''.join(d))


def integer(n):
    b = n.to_bytes(max(1, (n.bit_length() + 7) // 8), 'big')
    if b[0] & 128:
        b = b'\0' + b
    return tlv(2, b)


args = [a for a in sys.argv[1:]]
target = 'recovery'
if '--target' in args:
    i = args.index('--target')
    target = args[i + 1]
    del args[i:i + 2]
assert target in ('recovery', 'boot')
src = Path(args[0]) if len(args) > 0 else kd / 'kyf37-keitai-recovery-unsigned.img'
dst = Path(args[1]) if len(args) > 1 else kd / ('kyf37-keitai-recovery-owner-signed.img' if target == 'recovery' else 'kyf37-keitai-recovery-BOOTSLOT-owner-signed.img')
private = serialization.load_pem_private_key((dev / 'owner-signing-key.pem').read_bytes(), password=None)
public = private.public_key()
b, f, end = boot_parts(src)
tb, _, te = boot_parts(p.parent / 'phone-backup/kyf37-root-backup' / (target + '.img'))
_, payload, _, _ = read_tlv(tb, te)
sig = children(payload)
assert len(sig) == 5
attr = seq(tlv(0x13, b'/' + target.encode()), integer(end))
signed = private.sign(b[:end] + attr, padding.PKCS1v15(), hashes.SHA256())
env = seq(sig[0][2], sig[1][2], sig[2][2], attr, tlv(4, signed))
res = b[:end] + env
assert len(res) <= 16777216
res += bytes(16777216 - len(res))
public.verify(signed, res[:end] + attr, padding.PKCS1v15(), hashes.SHA256())
dst.write_bytes(res)
rep = {'target': target, 'unsigned': str(src), 'signed': str(dst), 'body_bytes': end, 'partition_bytes': len(res),
       'sha256': hashlib.sha256(res).hexdigest(), 'md5': hashlib.md5(res).hexdigest(),
       'unsigned_sha256': hashlib.sha256(src.read_bytes()).hexdigest()}
(kd / ('keitai-signing-manifest-%s.json' % target)).write_text(json.dumps(rep, indent=2))
print(json.dumps(rep, indent=2))
