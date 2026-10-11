#!/usr/bin/env python3
"""KYF37: add the offscreen GLES benchmark (device-inspection/gpu/gles_bench.cpp) as module kyf37_gles_bench (idempotent, WSL)."""
import os, shutil
d = os.path.expanduser('~/kyf37-android10/device/kyocera/kyf37/gpu-bench')
os.makedirs(d, exist_ok=True)
src = '/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/gpu'
shutil.copy(src + '/gles_bench.cpp', d + '/gles_bench.cpp')
shutil.copy(src + '/Android.bp.kyf37-gles-bench', d + '/Android.bp')
print('ok', d)
# camera snapshot test binary (module kyf37_cam_snap_test) shares the directory
shutil.copy(src + '/cam_snap_test.cpp', d + '/cam_snap_test.cpp')
bp = d + '/Android.bp'
t = open(bp).read()
if 'kyf37_cam_snap_test' not in t:
    open(bp, 'w').write(t.rstrip(chr(10)) + chr(10) + chr(10) + open(src + '/Android.bp.kyf37-cam-snap').read())
print('cam snap test staged')
# dlopen tester
shutil.copy(src + '/dlopen_test.cpp', d + '/dlopen_test.cpp')
t = open(bp).read()
if 'kyf37_dlopen_test' not in t:
    open(bp, 'w').write(t.rstrip(chr(10)) + chr(10) + chr(10) + open(src + '/Android.bp.kyf37-dlopen').read())
print('dlopen test staged')
# JPEG compat shim library
shutil.copy(src + '/jpegcompat.cpp', d + '/jpegcompat.cpp')
t = open(bp).read()
if 'libkyf37_jpegcompat' not in t:
    open(bp, 'w').write(t.rstrip(chr(10)) + chr(10) + chr(10) + open(src + '/Android.bp.kyf37-jpegcompat').read())
print('jpegcompat staged')
# GPS test tool (java_library kyf37_gpstest -> /system/framework/kyf37_gpstest.jar)
shutil.copy(src + '/GpsTest.java', d + '/GpsTest.java')
t = open(bp).read()
if 'kyf37_gpstest' not in t:
    open(bp, 'w').write(t.rstrip(chr(10)) + chr(10) + chr(10) + open(src + '/Android.bp.kyf37-gpstest').read())
print('gps test staged')
