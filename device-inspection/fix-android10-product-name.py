from pathlib import Path
device=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
(device/'AndroidProducts.mk').write_text('PRODUCT_MAKEFILES := lineage_kyf37:$(LOCAL_DIR)/lineage.mk\nCOMMON_LUNCH_CHOICES := lineage_kyf37-userdebug\n')
(device/'vendorsetup.sh').write_text('# Lunch choices are declared in AndroidProducts.mk.\n')
