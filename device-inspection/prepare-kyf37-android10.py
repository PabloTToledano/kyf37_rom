"""Generate an isolated Android10 legacy-board product; no phone operations."""
from pathlib import Path
import shutil,subprocess
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
tree=Path('/home/pablo/kyf37-android10')
subprocess.run(['python3',str(host/'device-inspection/prepare-kyf37-lineage.py'),'--tree',str(tree),'--android10'],check=True)
device=tree/'device/kyocera/kyf37'
board=device/'BoardConfig.mk'
board.write_text(board.read_text()+'''\n# Android 10 legacy, non-Treble product with original partition layout.
TARGET_COPY_OUT_VENDOR := system/vendor
BOARD_BUILD_SYSTEM_ROOT_IMAGE := false
BOARD_BOOT_HEADER_VERSION := 0
TARGET_USES_64_BIT_BINDER := false
BOARD_SEPOLICY_VERS := 30
BOARD_VNDK_VERSION :=
BOARD_KERNEL_IMAGE_NAME := zImage
TARGET_USES_HWC2 := false
TARGET_USES_GRALLOC1 := false
BOARD_AVB_ENABLE := false
''')
# Android10 product selection uses COMMON_LUNCH_CHOICES rather than vendorsetup.
(device/'AndroidProducts.mk').write_text('PRODUCT_MAKEFILES := lineage_kyf37:$(LOCAL_DIR)/lineage.mk\nCOMMON_LUNCH_CHOICES := lineage_kyf37-userdebug\n')
product=device/'lineage.mk'
text=product.read_text().replace('vendor/lineage/config/common_mini_phone.mk','vendor/lineage/config/common_full_phone.mk')
# Android 10 framework/resource behavior for upgraded legacy vendor hardware.
text+='''\nPRODUCT_SHIPPING_API_LEVEL := 22
PRODUCT_ENFORCE_VINTF_MANIFEST := false
PRODUCT_PROPERTY_OVERRIDES += ro.kyf37.android10_bringup=true
'''
product.write_text(text)
shutil.copytree(device,host/'kyf37-rom/device-android10',dirs_exist_ok=True)
print('Prepared isolated Android10 product; kernel and hardware wrappers still need integration')
