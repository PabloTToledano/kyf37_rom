$(call inherit-product, $(SRC_TARGET_DIR)/product/core_minimal.mk)
$(call inherit-product, vendor/omni/config/common.mk)
PRODUCT_DEVICE := kyf37
PRODUCT_NAME := omni_kyf37
PRODUCT_BRAND := KYOCERA
PRODUCT_MODEL := KYF37
PRODUCT_MANUFACTURER := KYOCERA
PRODUCT_COPY_FILES += device/kyocera/kyf37/recovery.fstab:recovery/root/etc/recovery.fstab
