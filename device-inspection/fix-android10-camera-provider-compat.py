"""Patch Camera HIDL Provider & Device 1.0 to zero-initialize camera_info structs and provide safe orientation/version defaults.
This eliminates uninitialized orientation pointer values (-1459479568) in dumpsys media.camera and uninitialized device_version.
WSL; idempotent.
"""
from pathlib import Path

tree = Path('/home/pablo/kyf37-android10')

# 1. Patch CameraDevice.cpp
dev_cpp = tree / 'hardware/interfaces/camera/device/1.0/default/CameraDevice.cpp'
text = dev_cpp.read_text()

# Ensure memset(&info, 0, sizeof(info)) in getCameraInfo
target1 = '''Return<void> CameraDevice::getCameraInfo(getCameraInfo_cb _hidl_cb) {
    Status status = initStatus();
    CameraInfo cameraInfo;
    if (status == Status::OK) {
        struct camera_info info;
        int ret = mModule->getCameraInfo(mCameraIdInt, &info);
        if (ret == OK) {
            cameraInfo.facing = (CameraFacing) info.facing;
            // Device 1.0 does not support external camera facing.
            // The closest approximation would be front camera.
            if (cameraInfo.facing == CameraFacing::EXTERNAL) {
                cameraInfo.facing = CameraFacing::FRONT;
            }
            cameraInfo.orientation = info.orientation;'''

replacement1 = '''Return<void> CameraDevice::getCameraInfo(getCameraInfo_cb _hidl_cb) {
    Status status = initStatus();
    CameraInfo cameraInfo;
    if (status == Status::OK) {
        struct camera_info info;
        memset(&info, 0, sizeof(info));
        int ret = mModule->getCameraInfo(mCameraIdInt, &info);
        if (ret == OK) {
            cameraInfo.facing = (CameraFacing) info.facing;
            // Device 1.0 does not support external camera facing.
            // The closest approximation would be front camera.
            if (cameraInfo.facing == CameraFacing::EXTERNAL) {
                cameraInfo.facing = CameraFacing::FRONT;
            }
            if (info.orientation != 0 && info.orientation != 90 &&
                info.orientation != 180 && info.orientation != 270) {
                cameraInfo.orientation = 90; // Default KYF37 rear sensor orientation
            } else {
                cameraInfo.orientation = info.orientation;
            }'''

if target1 in text:
    text = text.replace(target1, replacement1, 1)

# Ensure memset(&info, 0, sizeof(info)) in open()
target2 = '''Return<Status> CameraDevice::open(const sp<ICameraDeviceCallback>& callback) {
    ALOGI("Opening camera %s", mCameraId.c_str());
    Mutex::Autolock _l(mLock);

    camera_info info;
    status_t res = mModule->getCameraInfo(mCameraIdInt, &info);'''

replacement2 = '''Return<Status> CameraDevice::open(const sp<ICameraDeviceCallback>& callback) {
    ALOGI("Opening camera %s", mCameraId.c_str());
    Mutex::Autolock _l(mLock);

    camera_info info;
    memset(&info, 0, sizeof(info));
    status_t res = mModule->getCameraInfo(mCameraIdInt, &info);
    if (info.device_version == 0) {
        info.device_version = CAMERA_DEVICE_API_VERSION_1_0;
    }'''

if target2 in text:
    text = text.replace(target2, replacement2, 1)

dev_cpp.write_text(text)
print("Patched CameraDevice.cpp")

# 2. Patch LegacyCameraProviderImpl_2_4.cpp
prov_cpp = tree / 'hardware/interfaces/camera/provider/2.4/default/LegacyCameraProviderImpl_2_4.cpp'
ptext = prov_cpp.read_text()

ptarget = '''    mNumberOfLegacyCameras = mModule->getNumberOfCameras();
    for (int i = 0; i < mNumberOfLegacyCameras; i++) {
        struct camera_info info;
        auto rc = mModule->getCameraInfo(i, &info);
        if (rc != NO_ERROR) {
            ALOGE("%s: Camera info query failed!", __func__);
            mModule.clear();
            return true;
        }

        if (checkCameraVersion(i, info) != OK) {'''

preplacement = '''    mNumberOfLegacyCameras = mModule->getNumberOfCameras();
    for (int i = 0; i < mNumberOfLegacyCameras; i++) {
        struct camera_info info;
        memset(&info, 0, sizeof(info));
        auto rc = mModule->getCameraInfo(i, &info);
        if (rc != NO_ERROR) {
            ALOGE("%s: Camera info query failed!", __func__);
            mModule.clear();
            return true;
        }

        if (info.device_version == 0) {
            info.device_version = CAMERA_DEVICE_API_VERSION_1_0;
        }

        if (checkCameraVersion(i, info) != OK) {'''

if ptarget in ptext:
    ptext = ptext.replace(ptarget, preplacement, 1)

prov_cpp.write_text(ptext)
print("Patched LegacyCameraProviderImpl_2_4.cpp")
