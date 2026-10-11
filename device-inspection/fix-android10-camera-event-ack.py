#!/usr/bin/env python3
"""
fix-android10-camera-event-ack.py

Patches get_sensor_info (0x3504) and get_cam_info (0x3a58) in libmmcamera_interface.so
to ensure cam_info[0] is populated with valid static sensor info:
  facing = 0 (CAMERA_FACING_BACK)
  orientation = 90
  device_version = 0x100 (CAMERA_DEVICE_API_VERSION_1_0)
  static_camera_characteristics = NULL

All kernel ioctls (VIDIOC_QUERYCAP at 0x3e80, wait_for_event at 0x47b0) are kept STOCK
so that mm-qcamera-daemon and kernel v4l2 drivers negotiate camera capabilities properly.
"""

import os
import sys

TARGET_PATHS = [
    "/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary/lib/libmmcamera_interface.so",
    "/home/pablo/kyf37-android10/out/target/product/kyf37/system/lib/libmmcamera_interface.so",
]

# 1. get_sensor_info static info population
# Target address 0xc13c: facing=0, orientation=90, device_version=0x100
SENSOR_INFO_OFFSET = 0x3504
SENSOR_INFO_PATCH = bytes([
    0x06, 0x4b,             # 3504: ldr r3, [pc, #24] @ (3520)
    0x7b, 0x44,             # 3506: add r3, pc
    0x00, 0x21,             # 3508: movs r1, #0
    0x19, 0x60,             # 350a: str r1, [r3, #0] (facing = BACK)
    0x5a, 0x21,             # 350c: movs r1, #90
    0x59, 0x60,             # 350e: str r1, [r3, #4] (orientation = 90)
    0x4f, 0xf4, 0x80, 0x71, # 3510: mov.w r1, #256 (device_version = 0x100)
    0x99, 0x60,             # 3514: str r1, [r3, #8]
    0x00, 0x21,             # 3516: movs r1, #0
    0xd9, 0x60,             # 3518: str r1, [r3, #12] (static_characteristics = 0)
    0x18, 0x46,             # 351a: mov r0, r3
    0x70, 0x47,             # 351c: bx lr
    0xc0, 0x46,             # 351e: nop
    0x32, 0x8c, 0x00, 0x00  # 3520: .word 0x8c32 (offset to 0xc13c from 0x350a)
])

# 2. get_cam_info direct branch to 0x3504
CAM_INFO_OFFSET = 0x3a58
CAM_INFO_PATCH = bytes([
    0xff, 0xf7, 0x54, 0xbd  # 3a58: b.w 0x3504
])

assert len(SENSOR_INFO_PATCH) == 32
assert len(CAM_INFO_PATCH) == 4

def patch_file(path):
    if not os.path.exists(path):
        print(f"Skipping non-existent: {path}")
        return False

    with open(path, "rb") as f:
        data = bytearray(f.read())

    current_sinfo = bytes(data[SENSOR_INFO_OFFSET:SENSOR_INFO_OFFSET + 32])
    current_cinfo = bytes(data[CAM_INFO_OFFSET:CAM_INFO_OFFSET + 4])

    if current_sinfo == SENSOR_INFO_PATCH and current_cinfo == CAM_INFO_PATCH:
        print(f"Already patched: {path}")
        return True

    data[SENSOR_INFO_OFFSET:SENSOR_INFO_OFFSET + 32] = SENSOR_INFO_PATCH
    data[CAM_INFO_OFFSET:CAM_INFO_OFFSET + 4] = CAM_INFO_PATCH

    with open(path, "wb") as f:
        f.write(data)

    print(f"Successfully patched: {path}")
    return True

def main():
    success = True
    for p in TARGET_PATHS:
        if not patch_file(p):
            success = False

    if success:
        print("Patch applied cleanly to build tree.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
