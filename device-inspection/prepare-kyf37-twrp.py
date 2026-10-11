"""Create KYF37 build files and add keypad navigation to upstream TWRP."""
from pathlib import Path
import shutil
import re

root = Path('/home/pablo/kyf37-twrp')
host = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
device = root / 'device/kyocera/kyf37'
device.mkdir(parents=True, exist_ok=True)
shutil.copyfile(host/'device-inspection/recovery-stock/kernel', device/'kernel')
dt=host/'device-inspection/kyf37-mtp-dt.img'
if not dt.exists(): dt=host/'device-inspection/recovery-stock/dt'
shutil.copyfile(dt, device/'dt.img')
files = {
'AndroidProducts.mk': 'PRODUCT_MAKEFILES := $(LOCAL_DIR)/omni_kyf37.mk\n',
'vendorsetup.sh': 'add_lunch_combo omni_kyf37-eng\n',
'omni_kyf37.mk': '''$(call inherit-product, $(SRC_TARGET_DIR)/product/core_minimal.mk)
$(call inherit-product, vendor/omni/config/common.mk)
PRODUCT_DEVICE := kyf37
PRODUCT_NAME := omni_kyf37
PRODUCT_BRAND := KYOCERA
PRODUCT_MODEL := KYF37
PRODUCT_MANUFACTURER := KYOCERA
PRODUCT_COPY_FILES += device/kyocera/kyf37/recovery.fstab:recovery/root/etc/recovery.fstab
''',
'BoardConfig.mk': '''TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_VARIANT := cortex-a7
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_BOARD_PLATFORM := msm8909
TARGET_BOOTLOADER_BOARD_NAME := KYF37
TARGET_NO_BOOTLOADER := true
TARGET_PREBUILT_KERNEL := device/kyocera/kyf37/kernel
TARGET_CUSTOM_KERNEL_HEADERS := bootable/recovery/minuitwrp/include
BOARD_KERNEL_BASE := 0x80000000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_KERNEL_OFFSET := 0x00008000
BOARD_RAMDISK_OFFSET := 0x01000000
BOARD_TAGS_OFFSET := 0x00000100
BOARD_KERNEL_CMDLINE := console=ttyHSL0,115200,n8 no_console_suspend=1 androidboot.console=ttyHSL0 androidboot.hardware=qcom user_debug=31 msm_rtb.filter=0x3F ehci-hcd.park=3 androidboot.bootdevice=7824900.sdhci lpm_levels.sleep_disabled=1 earlyprintk androidboot.selinux=permissive
BOARD_MKBOOTIMG_ARGS := --ramdisk_offset 0x01000000 --tags_offset 0x00000100 --dt device/kyocera/kyf37/dt.img
BOARD_BOOTIMAGE_PARTITION_SIZE := 16777216
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 16777216
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1612709888
BOARD_USERDATAIMAGE_PARTITION_SIZE := 432?0000
BOARD_FLASH_BLOCK_SIZE := 131072
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_RECOVERY_FSTAB := device/kyocera/kyf37/recovery.fstab
RECOVERY_VARIANT := twrp
TW_THEME := portrait_mdpi
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TW_TARGET_USES_QCOM_BSP := false
TW_NEW_ION_HEAP := true
RECOVERY_GRAPHICS_FORCE_USE_LINELENGTH := true
TW_SCREEN_BLANK_ON_BOOT := true
TW_NO_SCREEN_TIMEOUT := true
TW_NO_REBOOT_BOOTLOADER := true
TW_EXCLUDE_SUPERSU := true
TW_EXCLUDE_MTP := true
TW_EXTRA_LANGUAGES := false
TW_KYF37_DPAD := true
TW_BRIGHTNESS_PATH := /sys/class/leds/lcd-backlight/brightness
TW_MAX_BRIGHTNESS := 255
TW_DEFAULT_BRIGHTNESS := 160
TW_INCLUDE_CRYPTO := false
''',
'recovery.fstab': '''/system ext4 /dev/block/bootdevice/by-name/system flags=display="System";backup=1
/data ext4 /dev/block/bootdevice/by-name/userdata flags=length=-16384;display="Data";backup=1
/misc emmc /dev/block/bootdevice/by-name/misc
/cache ext4 /dev/block/bootdevice/by-name/cache flags=display="Cache";backup=1
/boot emmc /dev/block/bootdevice/by-name/boot flags=display="Boot";backup=1
/recovery emmc /dev/block/bootdevice/by-name/recovery flags=display="Recovery";backup=1
/external_sd vfat /dev/block/mmcblk1p1 /dev/block/mmcblk1 flags=display="MicroSD";storage;removable
/persist ext4 /dev/block/bootdevice/by-name/persist flags=display="Persist";backup=1
/modemst1 emmc /dev/block/bootdevice/by-name/modemst1 flags=display="Modemst1";backup=1
/modemst2 emmc /dev/block/bootdevice/by-name/modemst2 flags=display="Modemst2";backup=1
''',
'recovery/root/init.recovery.qcom.rc': '''# Start rescue ADB independently of GUI initialization.
on boot
    setprop service.adb.root 1
    setprop sys.usb.config adb
    write /sys/class/android_usb/android0/enable 1
    start adbd
    write /sys/class/leds/lcd-backlight/brightness 160
'''
}
import json
parts=json.loads((host/'phone-backup/partition-map.json').read_text())['partitions']
data_size=next(p['bytes'] for p in parts if p['name']=='userdata')
files['BoardConfig.mk']=files['BoardConfig.mk'].replace('432?0000',str(data_size))
for name, content in files.items():
    (device/name).parent.mkdir(parents=True,exist_ok=True)
    (device/name).write_text(content)

events=root/'bootable/recovery/minuitwrp/events.cpp'
s=events.read_text()
if '// KYF37 matrix keypad is not a touchscreen' not in s:
    anchor='    if (e->ignored)     return 1;'
    assert anchor in s
    s=s.replace(anchor,anchor+'''
#ifdef TW_KYF37_DPAD
    // KYF37 matrix keypad is not a touchscreen despite its ABS capability.
    if (strstr(e->deviceName, "matrix_keypad") && ev->type != EV_KEY)
        return 1;
#endif
''',1)
    events.write_text(s)

gui=root/'bootable/recovery/gui/gui.cpp'
s=gui.read_text()
if '// KYF37 keypad cursor' not in s:
    s=s.replace('private:\n\t// timeouts', '''private:
#ifdef TW_KYF37_DPAD
    // KYF37 keypad cursor: physical arrows move, held center drags.
    int dpad_arrow;
    void moveDpadCursor();
#endif
\t// timeouts''',1)
    s=s.replace('\t\tx = y = 0;', '''\t\tx = y = 0;
#ifdef TW_KYF37_DPAD
        dpad_arrow = 0;
#endif''',1)
    anchor='\tif (touch_status == TS_TOUCH_AND_HOLD && mtime > touch_hold_ms)'
    assert anchor in s
    s=s.replace(anchor,'''#ifdef TW_KYF37_DPAD
    if (dpad_arrow) {
        const int delay = key_status == KS_KEY_PRESSED ? key_hold_ms : key_repeat_ms;
        if (mtime > delay) {
            moveDpadCursor();
            key_status = KS_KEY_REPEAT;
            gettimeofday(&touchStart, NULL);
        }
        return;
    }
#endif
'''+anchor,1)
    anchor='void InputHandler::process_EV_KEY(input_event& ev)\n{'
    assert anchor in s
    s=s.replace(anchor,'''#ifdef TW_KYF37_DPAD
void InputHandler::moveDpadCursor()
{
    MouseCursor *cursor = PageManager::GetMouseCursor();
    const int step = 6; // cursor speed multiplier gives 15 pixels per step
    cursor->Move(dpad_arrow == KEY_LEFT ? -step : dpad_arrow == KEY_RIGHT ? step : 0,
                 dpad_arrow == KEY_UP ? -step : dpad_arrow == KEY_DOWN ? step : 0);
    cursor->GetPos(x, y);
}
#endif
'''+anchor+'''
#ifdef TW_KYF37_DPAD
    if (ev.code == KEY_UP || ev.code == KEY_DOWN || ev.code == KEY_LEFT || ev.code == KEY_RIGHT) {
        if (ev.value == 1) {
            dpad_arrow = ev.code;
            moveDpadCursor();
            key_status = KS_KEY_PRESSED;
            gettimeofday(&touchStart, NULL);
        } else if (!ev.value && dpad_arrow == ev.code) {
            dpad_arrow = 0;
            key_status = KS_NONE;
        }
        return;
    }
    if (ev.code == KEY_ENTER) {
        if (ev.value == 2) return;
        ev.code = BTN_LEFT;
    } else if (ev.code == 355) {
        ev.code = KEY_BACK;
    }
#endif
''',1)
    # Determine the upstream enum name rather than assuming it.
    if 'KS_KEY_REPEAT' not in s.split('enum key_status_enum')[1].split('};')[0]:
        s=s.replace('key_status = KS_KEY_REPEAT;', 'key_status = KS_KEY_REPEAT;')
    gui.write_text(s)

mouse=root/'bootable/recovery/gui/mousecursor.cpp'
s=mouse.read_text()
if 'TW_KYF37_DPAD' not in s:
    s=s.replace('m_present = false;', '''#ifdef TW_KYF37_DPAD
    m_present = true;
#else
    m_present = false;
#endif''',1)
    s=s.replace('if (m_present != ev_has_mouse())','''#ifndef TW_KYF37_DPAD
    if (m_present != ev_has_mouse())''',1)
    s=s.replace('\n\tif (m_present && m_moved)', '\n#endif\n\tif (m_present && m_moved)',1)
    s=s.replace('m_resX);', 'm_resX - 1);').replace('m_resY);','m_resY - 1);')
    mouse.write_text(s)
for name in ['gui/Android.mk','minuitwrp/Android.mk']:
    path=root/'bootable/recovery'/name
    s=path.read_text().replace('LOCAL_CFLAGS := -fno-strict-aliasing', 'LOCAL_CFLAGS += -fno-strict-aliasing')
    if '-DTW_KYF37_DPAD' not in s:
        anchor='include $(CLEAR_VARS)'
        s=s.replace(anchor,anchor+'\nifeq ($(TW_KYF37_DPAD),true)\nLOCAL_CFLAGS += -DTW_KYF37_DPAD\nendif\n',1)
        path.write_text(s)
shutil.copytree(device,host/'kyf37-twrp-device',dirs_exist_ok=True)
print('Device configuration and keypad patch prepared')

# Modern host headers define bool; rename this legacy field without changing ABI.
for package in ['external/libsepol','external/checkpolicy']:
    for path in (root/package).rglob('*'):
        if path.suffix not in ('.c','.h'): continue
        s=path.read_text()
        t=re.sub(r'(->|\.)bool\b',r'\1boolean_id',s)
        t=t.replace('uint32_t bool;', 'uint32_t boolean_id;')
        if t!=s: path.write_text(t)
checkpolicy=root/'external/checkpolicy/checkpolicy.c'
s=checkpolicy.read_text()
if not s.startswith('#include <ctype.h>'):
    checkpolicy.write_text('#include <ctype.h>\n'+s)
checkmk=root/'external/checkpolicy/Android.mk'
s=checkmk.read_text()
if '-std=gnu99' not in s:
    checkmk.write_text(s.replace('-Wall -Wshadow -O2','-std=gnu99 -Wall -Wshadow -O2',1))
header=root/'external/checkpolicy/checkpolicy.h'
s=header.read_text().replace('\nte_assert_t *te_assertions;', '\nextern te_assert_t *te_assertions;')
header.write_text(s)
define=root/'external/checkpolicy/policy_define.c'
s=define.read_text()
if '\nte_assert_t *te_assertions;' not in s:
    s=s.replace('#include "checkpolicy.h"','#include "checkpolicy.h"\nte_assert_t *te_assertions;',1)
    define.write_text(s)
definitions=root/'build/core/definitions.mk'
s=definitions.read_text()
old='$($(PRIVATE_2ND_ARCH_VAR_PREFIX)HOST_AR) p $(1) $$f > $$ldir/$$f;'
new='mkdir -p "$$(dirname "$$ldir/$$f")"; \\\n        $($(PRIVATE_2ND_ARCH_VAR_PREFIX)HOST_AR) pP $(1) $$f > $$ldir/$$f;'
if old in s: definitions.write_text(s.replace(old,new,1))
partition=root/'bootable/recovery/partition.cpp'
s=partition.read_text()
if 'sml != nullptr' in s:
    partition.write_text(s.replace('sml != nullptr','sml != NULL'))
