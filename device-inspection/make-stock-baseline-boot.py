"""Build an UNSIGNED diagnostic stock boot for the cellular baseline experiment (RADIO.md section 9).

Input : the owner-signed stock boot (phone-backup/pre-rom-20261007/boot.img), stock kernel + stock ramdisk.
Output: same kernel/DT, stock ramdisk with only these changes:
  * userdata is NOT mounted (removed from fstab.qcom); /data is a tmpfs, so the Android 10 userdata is never touched
  * default.prop: ro.secure=0 ro.adb.secure=0 ro.debuggable=1 persist.sys.usb.config=mtp,adb (root adb without keys)
  * service 'kycell' runs /kycell.sh which snapshots SMD channels, IPC-router servers, props, ps and logs into
    /cache/kycell/ at several times after boot
  * cmdline gets androidboot.selinux=permissive
Sign afterwards with sign-rom-boot.py (new output name). Never ship this image.
usage: python make-stock-baseline-boot.py <stock-boot.img> <out-unsigned.img>
"""
import gzip, struct, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
data = src.read_bytes()
assert data[:8] == b'ANDROID!'
ksz, kaddr, rsz, raddr, ssz, saddr, taddr, page, dtsz, unused = struct.unpack_from('<10I', data, 8)
name = data[48:64]; cmdline = data[64:576]; idv = data[576:608]
def blk(off, n): return data[off:off + n]
def pad(n): return (n + page - 1) // page * page
off = page
kernel = blk(off, ksz); off += pad(ksz)
ramdisk = blk(off, rsz); off += pad(rsz)
second = blk(off, ssz); off += pad(ssz)
dt = blk(off, dtsz)

# --- cpio newc ---
raw = gzip.decompress(ramdisk)
entries = []; p = 0
while True:
    hdr = raw[p:p + 110]; assert hdr[:6] == b'070701', hdr[:6]
    f = [int(hdr[6 + 8 * i:14 + 8 * i], 16) for i in range(13)]
    namesize, filesize = f[11], f[6]
    nm = raw[p + 110:p + 110 + namesize - 1].decode()
    p = (p + 110 + namesize + 3) & ~3
    body = raw[p:p + filesize]; p = (p + filesize + 3) & ~3
    if nm == 'TRAILER!!!': break
    entries.append([nm, f, body])
byname = {e[0]: e for e in entries}

def setfile(nm, body, mode=0o100644):
    if nm in byname:
        byname[nm][2] = body; byname[nm][1][6] = len(body); byname[nm][1][1] = mode
    else:
        f = [0, mode, 0, 0, 1, 0, len(body), 0, 0, 0, 0, 0, 0]
        e = [nm, f, body]; entries.append(e); byname[nm] = e

fstab = byname['fstab.qcom'][2].decode()
fstab = '\n'.join(l for l in fstab.split('\n') if 'by-name/userdata' not in l) + '\n'
setfile('fstab.qcom', fstab.encode(), byname['fstab.qcom'][1][1])

dp = byname['default.prop'][2].decode()
for k, v in (('ro.secure', '0'), ('ro.adb.secure', '0'), ('ro.debuggable', '1')):
    dp = dp.replace(f'{k}=1' if v == '0' else f'{k}=0', f'{k}={v}')
dp += 'persist.sys.usb.config=mtp,adb\n'
setfile('default.prop', dp.encode(), byname['default.prop'][1][1])

tr = byname['init.target.rc'][2].decode()
assert 'mount_all fstab.qcom' in tr
if 'kycell' not in tr:
    tr = tr.replace('    mount_all fstab.qcom\n',
                    '    mount_all fstab.qcom\n    mount tmpfs tmpfs /data mode=0771,uid=1000,gid=1000\n', 1)
    tr += ('\nservice kycell /system/bin/sh /kycell.sh\n    class core\n    user root\n    oneshot\n'
           '    seclabel u:r:init:s0\n')
setfile('init.target.rc', tr.encode(), byname['init.target.rc'][1][1])

script = r'''#!/system/bin/sh
mount -t debugfs debugfs /sys/kernel/debug 2>/dev/null
D=/cache/kycell; mkdir -p $D
n=0
for t in 15 30 30 45 60 120 180 300; do
  sleep $t; n=$((n+1)); F=$D/snap$n.txt
  { echo "=== uptime"; cat /proc/uptime
    echo "=== smd ch"; cat /sys/kernel/debug/smd/ch
    echo "=== ipc router servers"; cat /sys/kernel/debug/msm_ipc_router/dump_servers
    echo "=== dev"; ls -l /dev/smd* /dev/subsys*
    echo "=== ps"; ps
    echo "=== props"; getprop
  } > $F 2>&1
  dmesg > $D/dmesg$n.txt 2>&1
  logcat -d -b radio -v threadtime > $D/radio$n.txt 2>&1
  logcat -d -b main -b system -v threadtime > $D/main$n.txt 2>&1
  sync
done
'''
setfile('kycell.sh', script.encode(), 0o100750)

outc = bytearray(); ino = 300000
for nm, f, body in entries + [['TRAILER!!!', [0] * 13, b'']]:
    f = list(f)
    if nm == 'TRAILER!!!': f[4] = 1
    f[0] = ino; ino += 1
    f[11] = len(nm) + 1; f[6] = len(body)
    outc += b'070701' + b''.join(b'%08X' % v for v in f) + nm.encode() + b'\0'
    while len(outc) % 4: outc += b'\0'
    outc += body
    while len(outc) % 4: outc += b'\0'
newrd = gzip.compress(bytes(outc), 9)

cl = cmdline.rstrip(b'\0')
if b'androidboot.selinux=permissive' not in cl: cl += b' androidboot.selinux=permissive'
assert len(cl) < 512
hdr = bytearray(page)
hdr[:8] = b'ANDROID!'
struct.pack_into('<10I', hdr, 8, ksz, kaddr, len(newrd), raddr, ssz, saddr, taddr, page, dtsz, unused)
hdr[48:64] = name; hdr[64:64 + len(cl)] = cl; hdr[576:608] = idv
img = bytearray(hdr)
for b in (kernel, newrd, second, dt):
    img += b; img += b'\0' * (pad(len(b)) - len(b))
out.write_bytes(bytes(img))
print('wrote', out, len(img), 'ramdisk', len(newrd), 'cmdline', cl.decode())
