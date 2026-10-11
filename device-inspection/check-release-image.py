#!/usr/bin/env python3
"""Pre-flash gate for a KYF37 system image (raw ext4). Exits non-zero if the image contains anything known to break boot
or is missing pieces every release must have. Born from v17/v18: public.libraries-kyocera.txt (zygote abort -> no boot)
and FsDtvApp (crash loop, unresponsive phone) survived in the image as STALE files after their copy rules were removed
(Android's build never deletes installed files).

usage: check-release-image.py <system-android10.raw.img> [--boot <boot-android10-owner-signed.img>]
Run in WSL (needs debugfs)."""
import subprocess, sys, pathlib

FORBIDDEN = [  # path in image (system root), reason
    ('/etc/public.libraries-kyocera.txt', 'libnativeloader aborts zygote on non-company-suffixed names (v17 boot failure)'),
    ('/app/FsDtvApp', 'One Seg TV app crash-loops (UnsatisfiedLinkError libskia.so) and takes the screen'),
    ('/app/Kyf37Tv', 'TV app depends on the same missing TV stack'),
    ('/priv-app/FsDtvApp', 'TV app'),
    ('/priv-app/Kyf37Tv', 'TV app'),
    ('/app/MobileLight', 'obsolete flashlight duplicates the keypad replacement'),
]
REQUIRED = [  # path, why
    ('/vendor/lib/hw/lights.kyf37.so', 'brightness HAL in the vendor HIDL namespace'),
    ('/vendor/lib/libril.so', 'SIM/data compatibility library'),
    ('/app/Kyf37Flashlight/Kyf37Flashlight.apk', 'keypad flashlight replacement'),
    ('/app/Kyf37Dialer/Kyf37Dialer.apk', 'native keypad phone'),
    ('/app/Kyf37Messages/Kyf37Messages.apk', 'native keypad messages'),
    ('/app/Kyf37Contacts/Kyf37Contacts.apk', 'native keypad contacts'),
    ('/etc/public.libraries.txt', 'standard public library list'),
    ('/etc/init/init.kyf37.camera.rc', 'camera daemon/provider startup (jpeg shim preload)'),
    ('/vendor/lib/libkyf37_jpegcompat.so', 'stock JPEG stack compatibility shim for the camera'),
    ('/vendor/bin/lkspad', 'camera property store daemon'),
    ('/lib/modules/pronto/pronto_wlan.ko', 'Wi-Fi module'),
    ('/xbin/magisk', 'root'),
    ('/etc/kyf37-magisk.sh', 'root startup script'),
    ('/lib/libtinyalsa.so', 'audio (36-byte pcm_config ABI fix)'),
    ('/etc/permissions/privapp-permissions-microg.xml', 'privapp allowlist for microG (missing allowlist crashes system_server)'),
    ('/priv-app/GmsCore/GmsCore.apk', 'microG GmsCore service'),
    ('/priv-app/FakeStore/FakeStore.apk', 'microG companion FakeStore'),
    ('/priv-app/GsfProxy/GsfProxy.apk', 'microG Services Framework proxy'),
]

def debugfs(img, cmd):
    r = subprocess.run(['debugfs', '-R', cmd, img], capture_output=True, text=True)
    return r.stdout + r.stderr

def exists(img, path):
    out = debugfs(img, 'stat ' + path)
    return 'Inode:' in out

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    img = sys.argv[1]
    bad = 0
    print('image:', img)
    for p, why in FORBIDDEN:
        if exists(img, p):
            print('FAIL forbidden present:', p, '-', why); bad += 1
        else:
            print('ok   absent:', p)
    for p, why in REQUIRED:
        if exists(img, p):
            print('ok   present:', p)
            if p == '/priv-app/GmsCore/GmsCore.apk':
                st = debugfs(img, 'stat ' + p)
                sz = 0
                for line in st.splitlines():
                    if 'Size:' in line:
                        for token in line.split():
                            if token.isdigit():
                                sz = int(token)
                                break
                if sz < 100000000:
                    print('FAIL GmsCore size is %d bytes (expected unstripped official >100MB; stripped breaks official signature)' % sz)
                    bad += 1
                else:
                    print('ok   GmsCore size %d bytes (official unstripped signature preserved)' % sz)
        else:
            print('FAIL required missing:', p, '-', why); bad += 1
    # every priv-app needs an allowlist file somewhere in /etc/permissions
    pa = debugfs(img, 'ls -p /priv-app')
    n_priv = len([l for l in pa.splitlines() if l.count('/') >= 5 and not l.split('/')[5] in ('.', '..', '')])
    pm = debugfs(img, 'ls -p /etc/permissions')
    n_allow = len([l for l in pm.splitlines() if 'privapp-permissions' in l])
    print('info priv-app dirs:', n_priv, ' privapp-permissions files:', n_allow)
    if n_priv and not n_allow:
        print('FAIL priv-apps present but no privapp allowlists'); bad += 1
    if '--boot' in sys.argv:
        boot = pathlib.Path(sys.argv[sys.argv.index('--boot') + 1])
        data = boot.read_bytes()
        print('boot image size', len(data), 'signed-size ok' if len(data) == 16777216 else 'WARN unexpected size')
        if len(data) != 16777216:
            bad += 1
    print('RESULT:', 'FAIL (%d problems)' % bad if bad else 'PASS')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
