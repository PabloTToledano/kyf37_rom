#!/usr/bin/env python3
"""KYF37 camera boot integration (idempotent, run in WSL, after the other fix-android10-camera-*.py scripts):
 - ship stock Kyocera lkspad + its property store (ps_ro.dat/ps_rw.dat/libbfss.xml). Without the store lkspad answers
   '[AUTH_NG] key[rw_camdrv_temp_*] is unknown' and mm-qcamera-daemon reports an over-temperature error => camera aborts.
   The daemon also blocks ~5 s per capability query when /dev/socket/lkspad does not exist.
 - start mm-qcamera-daemon as camera:camera at boot (init.kyf37.camera.rc, 'override' beats ramdisk init.target.rc)
 - restart provider then cameraserver after the daemon is up (the framework otherwise keeps camera 0 NOT_PRESENT)
 - install the camera-fix kernel as the device prebuilt kernel (backup kept once)"""
import os, shutil, hashlib
home = os.path.expanduser('~')
tree = home + '/kyf37-android10'
dev = tree + '/device/kyocera/kyf37'
ven = tree + '/vendor/kyocera/kyf37'
stock = home + '/kyf37-rom/stock-system/vendor'
NL = chr(10)
# 1. blobs
mk = ven + '/kyf37-vendor.mk'
s = open(mk).read()
for rel in ['bin/lkspad', 'etc/ps_ro.dat', 'etc/ps_rw.dat', 'etc/libbfss.xml']:
    dst = ven + '/proprietary/vendor/' + rel
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copy2(stock + '/' + rel, dst)
    line = 'vendor/kyocera/kyf37/proprietary/vendor/' + rel + ':system/vendor/' + rel
    if line not in s:
        s = s.rstrip() + NL + 'PRODUCT_COPY_FILES += ' + line + NL
open(mk, 'w').write(s)
# 2. rc
rc = dev + '/init.kyf37.camera.rc'
new = """# The camera provider enumerates sensors once at start. The OEM daemon must already be running,
# otherwise Android reports zero cameras for the whole boot. After the provider restarts, cameraserver
# must restart too, or it keeps camera 0 in NOT_PRESENT ('State transition to the same status 0 not allowed').
service kyf37-camera-order /system/bin/sh -c "sleep 4; setprop ctl.restart vendor.camera-provider-2-4; sleep 8; setprop ctl.restart cameraserver"
    user root
    oneshot
    disabled

on property:init.svc.qcamerasvr=running
    start kyf37-camera-order

# Overrides the ramdisk init.target.rc definition (which has no seclabel => 'Could not get process context').
# Stock daemon, run unprivileged as camera so cameraserver/provider (group camera) can reach its socket.
service qcamerasvr /system/bin/mm-qcamera-daemon
    class late_start
    user camera
    group camera system inet input graphics
    seclabel u:r:init:s0
    override

# Provider override: the stock JPEG stack needs symbols Android 10 lacks (__aeabi_idiv0, EVP_Seal*/EVP_Open*); preload our shim.
service vendor.camera-provider-2-4 /vendor/bin/hw/android.hardware.camera.provider@2.4-service
    interface android.hardware.camera.provider@2.4::ICameraProvider legacy/0
    class hal
    user cameraserver
    group audio camera input drmrpc
    ioprio rt 4
    capabilities SYS_NICE
    writepid /dev/cpuset/camera-daemon/tasks /dev/stune/top-app/tasks
    setenv LD_PRELOAD /vendor/lib/libkyf37_jpegcompat.so
    override

# imglib/mm-jpeg read this to find a perf-lock client; the shim exports no-op perf_lock_acq/perf_lock_rel.
on post-fs-data
    setprop ro.vendor.extension_library /vendor/lib/libkyf37_jpegcompat.so
"""
if open(rc).read() != new:
    open(rc, 'w').write(new)
    print('rc written')
# 3. kernel
src = home + '/kyf37-rom/kernel-android10-gcc48-build/arch/arm/boot/zImage'
cur = dev + '/kernel'
bak = cur + '.pre-camerafix'
if not os.path.exists(bak):
    shutil.copy2(cur, bak)
if hashlib.sha256(open(cur, 'rb').read()).hexdigest() != hashlib.sha256(open(src, 'rb').read()).hexdigest():
    shutil.copy2(src, cur)
    print('kernel installed')

# PRODUCT_PACKAGES for the shim (built from device/kyocera/kyf37/gpu-bench, see fix-android10-gpu-bench.py)
dm = dev + '/device.mk'
t = open(dm).read()
if 'libkyf37_jpegcompat' not in t:
    open(dm, 'w').write(t.rstrip(chr(10)) + chr(10) + 'PRODUCT_PACKAGES += libkyf37_jpegcompat' + chr(10))
    print('device.mk: libkyf37_jpegcompat added')
