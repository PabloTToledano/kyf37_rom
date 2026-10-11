#!/usr/bin/env python3
"""KYF37: legacy QCamera HAL calls get_memory(fd,size,n,user) with user = its own QCameraStreamMemory*, because the old
CameraHardwareInterface ignored 'user'. The Android 10 HIDL CameraDevice::sGetMemory casts user to CameraDevice* and
crashes (SEGV in CAM_defrdWrk). Use the device that registered the callbacks instead. WSL, idempotent."""
import os
p = os.path.expanduser('~/kyf37-android10/hardware/interfaces/camera/device/1.0/default/CameraDevice.cpp')
s = open(p).read()
if 'kyf37ActiveDevice' in s:
    print('already'); raise SystemExit
a = 'camera_memory_t* CameraDevice::sGetMemory(int fd, size_t buf_size, uint_t num_bufs, void *user) {'
assert s.count(a) == 1
s = s.replace(a, '// KYF37: see fix-android10-camera-getmemory-cookie.py' + chr(10) + 'static CameraDevice* kyf37ActiveDevice = nullptr;' + chr(10) + chr(10) + a)
b = '    CameraDevice* object = static_cast<CameraDevice*>(user);' + chr(10) + '    if (object->mDeviceCallback == nullptr) {' + chr(10) + '        ALOGE("%s: camera HAL request memory while camera is not opened!"'
assert s.count(b) == 1
s = s.replace(b, '    CameraDevice* object = kyf37ActiveDevice ? kyf37ActiveDevice : static_cast<CameraDevice*>(user);' + b[len('    CameraDevice* object = static_cast<CameraDevice*>(user);'):])
c = 'sNotifyCb, sDataCb, sDataCbTimestamp, sGetMemory, this);'
assert s.count(c) == 1
i = s.index(c)
j = s.rfind('if (mDevice->ops->set_callbacks) {', 0, i)
j = s.rfind(chr(10), 0, j) + 1
s = s[:j] + '    kyf37ActiveDevice = this;' + chr(10) + s[j:]
open(p, 'w').write(s); print('patched')
