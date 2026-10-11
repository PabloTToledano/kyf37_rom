#!/usr/bin/env python3
"""
fix-android10-camera-c2d-libs.py

Copies Qualcomm 2D GPU acceleration libraries (libC2D2.so, libc2d30-a3xx.so, libc2d30-a4xx.so)
required by libmmcamera2_c2d_module.so to the vendor proprietary tree and build output.
Without these, the camera postproc module fails to dlopen libC2D2.so, aborting the camera session.
"""

import os
import shutil
import sys

STOCK_VENDOR_LIB = "/home/pablo/kyf37-rom/stock-system/vendor/lib"
PROP_VENDOR_LIB = "/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary/vendor/lib"
OUT_VENDOR_LIB = "/home/pablo/kyf37-android10/out/target/product/kyf37/system/vendor/lib"
VENDOR_MK = "/home/pablo/kyf37-android10/vendor/kyocera/kyf37/kyf37-vendor.mk"
PROP_FILES_TXT = "/home/pablo/kyf37-android10/device/kyocera/kyf37/proprietary-files.txt"

LIBS = [
    "libC2D2.so",
    "libc2d30-a3xx.so",
    "libc2d30-a4xx.so"
]

def main():
    copied = 0
    for lib in LIBS:
        src = os.path.join(STOCK_VENDOR_LIB, lib)
        if not os.path.exists(src):
            print(f"ERROR: Missing stock source {src}")
            continue

        for dest_dir in [PROP_VENDOR_LIB, OUT_VENDOR_LIB]:
            if os.path.exists(dest_dir):
                dst = os.path.join(dest_dir, lib)
                shutil.copy2(src, dst)
                print(f"Copied {lib} -> {dst}")
                copied += 1

    # Ensure listed in kyf37-vendor.mk
    if os.path.exists(VENDOR_MK):
        with open(VENDOR_MK, "r") as f:
            content = f.read()

        changed = False
        for lib in LIBS:
            entry = f"vendor/kyocera/kyf37/proprietary/vendor/lib/{lib}:system/vendor/lib/{lib}"
            if entry not in content:
                # Add to PRODUCT_COPY_FILES
                content += f"\nPRODUCT_COPY_FILES += \\\n    {entry}\n"
                changed = True
                print(f"Added {lib} to {VENDOR_MK}")

        if changed:
            with open(VENDOR_MK, "w") as f:
                f.write(content)

    print(f"Done. Copied {copied} files.")

if __name__ == "__main__":
    main()
