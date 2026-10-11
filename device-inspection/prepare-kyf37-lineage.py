from pathlib import Path
import json,shutil,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--tree',default='/home/pablo/kyf37-lineage')
parser.add_argument('--oreo',action='store_true')
parser.add_argument('--android10',action='store_true')
args=parser.parse_args()
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms');tree=Path(args.tree);d=tree/'device/kyocera/kyf37';d.mkdir(parents=True,exist_ok=True)
twrp=host/'kyf37-twrp-device';stock=Path('/home/pablo/kyf37-rom/stock-system');boot=host/'kyf37-rom/stock-boot-ramdisk'
shutil.copytree(host/'kyf37-rom/selector-source/res',
 d/'overlay/frameworks/base/core/res/res',dirs_exist_ok=True)
shutil.copytree(host/'kyf37-rom/shared-resource-source/res',
 d/'overlay/frameworks/base/core/res/res',dirs_exist_ok=True)
# framework-res does not consume PRODUCT_AAPT_FLAGS. Declare resource additions
# explicitly so model-only resources can be merged without guessed public IDs.
import xml.etree.ElementTree as ET
added=set()
for source in ('selector-source/res','shared-resource-source/res'):
 for asset in (host/'kyf37-rom'/source).rglob('*'):
  if not asset.is_file():continue
  kind=asset.parent.name.split('-')[0]
  if kind=='values':
   for entry in ET.parse(asset).getroot():
    if entry.get('name'):added.add((entry.get('type',entry.tag),entry.get('name')))
  else:added.add((kind,asset.name.split('.')[0]))
declarations=ET.Element('resources')
for kind,name in sorted(added):ET.SubElement(declarations,'add-resource',{'type':kind,'name':name})
dest=d/'overlay/frameworks/base/core/res/res/values/kyf37_additions.xml'
dest.parent.mkdir(parents=True,exist_ok=True)
ET.ElementTree(declarations).write(dest,encoding='utf-8',xml_declaration=True)
for f in ['kernel','dt.img']:shutil.copy2(twrp/f,d/f)
shutil.copy2(stock/'media/bootanimation.zip',d/'bootanimation.zip')
board=(twrp/'BoardConfig.mk').read_text();board='\n'.join(l for l in board.splitlines() if not l.startswith(('TW_','RECOVERY_VARIANT','TARGET_RECOVERY_PIXEL_FORMAT','TARGET_RECOVERY_FSTAB','TARGET_CUSTOM_KERNEL_HEADERS','RECOVERY_GRAPHICS_')))+'\n'
board += """TARGET_BOOTANIMATION := device/kyocera/kyf37/bootanimation.zip
TARGET_SCREEN_WIDTH := 480
TARGET_SCREEN_HEIGHT := 854
BOARD_USES_QCOM_HARDWARE := true
TARGET_USES_ION := true
KYF37_USE_STOCK_VIDEO_CODECS := true
KYF37_USE_STOCK_RMNET := true
# Recovery is maintained separately as owner-signed, keypad-enabled TWRP.
# Do not construct a replacement recovery or boot-to-recovery patch in this ROM.
TARGET_NO_RECOVERY := true
TARGET_BOARD_PLATFORM_GPU := qcom-adreno304
BOARD_USES_ALSA_AUDIO := true
BOARD_HAVE_BLUETOOTH := true
BOARD_HAVE_BLUETOOTH_QCOM := true
BOARD_WLAN_DEVICE := qcwcn
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
BOARD_HOSTAPD_DRIVER := NL80211
BOARD_WPA_SUPPLICANT_PRIVATE_LIB := lib_driver_cmd_qcwcn
BOARD_HOSTAPD_PRIVATE_LIB := lib_driver_cmd_qcwcn
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_SEPOLICY_DIRS += device/kyocera/kyf37/sepolicy
DEVICE_PACKAGE_OVERLAYS += device/kyocera/kyf37/overlay
"""
(d/'BoardConfig.mk').write_text(board)
(d/'sepolicy').mkdir(exist_ok=True)
(d/'sepolicy/kyf37_outer_screen.te').write_text('''type kyf37_outer_screen, domain;
app_domain(kyf37_outer_screen)
allow kyf37_outer_screen system_app_data_file:dir create_dir_perms;
allow kyf37_outer_screen system_app_data_file:{ file lnk_file } create_file_perms;
type kyf37_subdisplay_device, dev_type;
allow kyf37_outer_screen graphics_device:dir search;
allow kyf37_outer_screen kyf37_subdisplay_device:chr_file rw_file_perms;
get_prop(kyf37_outer_screen, system_prop)
''')
(d/'sepolicy/file_contexts').write_text('/dev/graphics/fb1 u:object_r:kyf37_subdisplay_device:s0\n')
(d/'sepolicy/seapp_contexts').write_text('user=system seinfo=platform name=org.kyf37.subdisplay domain=kyf37_outer_screen type=system_app_data_file\n')
(d/'AndroidProducts.mk').write_text('PRODUCT_MAKEFILES := lineage_kyf37:$(LOCAL_DIR)/lineage.mk\n')
(d/'vendorsetup.sh').write_text('add_lunch_combo lineage_kyf37-userdebug\n')
(d/'lineage.mk').write_text("""$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, vendor/cm/config/common_mini_phone.mk)
$(call inherit-product, device/kyocera/kyf37/device.mk)
PRODUCT_NAME := lineage_kyf37
PRODUCT_DEVICE := kyf37
PRODUCT_BRAND := KYOCERA
PRODUCT_MANUFACTURER := KYOCERA
PRODUCT_MODEL := KYF37
PRODUCT_GMS_CLIENTID_BASE := android-kyocera
""")
if args.oreo or args.android10:
 p=d/'lineage.mk'
 p.write_text(p.read_text().replace('vendor/cm/','vendor/lineage/')+
  '\n$(call inherit-product, build/target/product/go_defaults.mk)\n')
copy=[]
ramdisk=d/'ramdisk';ramdisk.mkdir(exist_ok=True)
for p in boot.iterdir():
 if p.suffix in ['.rc','.sh'] and p.name not in ['init.rc','init.zygote32.rc','init.environ.rc','init.usb.rc','init.trace.rc','ueventd.rc']:
  shutil.copy2(p,ramdisk/p.name);copy.append('device/kyocera/kyf37/ramdisk/'+p.name+':root/'+p.name)
with (ramdisk/'init.qcom.rc').open('a') as f:
 f.write('\nimport /init.kc.common.rc\nimport /init.kc.model.rc\n')
# Do not copy stock init binary, boot classpath, recovery repair, or userdata encryption policy.
f=(boot/'fstab.qcom').read_text();f=f.replace('wait,check,encryptable=/persist/udf','wait,check').replace('wait,check,kfmmskip','wait,check')
(ramdisk/'fstab.qcom').write_text(f);copy.append('device/kyocera/kyf37/ramdisk/fstab.qcom:root/fstab.qcom')
for p in (stock/'usr/keylayout').glob('*.kl'):
 if p.name in ['matrix_keypad_67.kl','gpio-keys.kl','qpnp_pon.kl','swic_hs_key.kl']:
  dest=d/'keylayout'/p.name;dest.parent.mkdir(exist_ok=True);text=p.read_text()
  if p.name=='matrix_keypad_67.kl':text=text.replace('key 61      F3','key 61      HOME')
  dest.write_text(text);copy.append('device/kyocera/kyf37/keylayout/'+p.name+':system/usr/keylayout/'+p.name)
# Preserve the actual OEM feedback recordings rather than the generic AOSP set.
# Prepend entries so duplicate inherited AOSP destinations select OEM files.
sound_copy=[]
root_start=d/'init.qcom.rootagent.sh'
shutil.copy2(host/'device-inspection/init.qcom.rootagent.sh',root_start)
copy.append('device/kyocera/kyf37/init.qcom.rootagent.sh:system/etc/init.qcom.rootagent.sh')
shutil.copy2(host/'device-inspection/enable-rom-app-root.sh',d/'enable-rom-app-root.sh')
copy.append('device/kyocera/kyf37/enable-rom-app-root.sh:system/etc/enable-rom-app-root.sh')
for audio in sorted((stock/'media/audio/ui').iterdir()):
 if audio.is_file():
  target=d/'audio/ui'/audio.name;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(audio,target)
  sound_copy.append('device/kyocera/kyf37/audio/ui/'+audio.name+':system/media/audio/ui/'+audio.name)
(d/'device.mk').write_text("""$(call inherit-product, frameworks/native/build/phone-xhdpi-1024-dalvik-heap.mk)
$(call inherit-product, vendor/kyocera/kyf37/kyf37-vendor.mk)
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := hdpi
PRODUCT_AAPT_FLAGS += --auto-add-overlay
PRODUCT_CHARACTERISTICS := phone
PRODUCT_PACKAGES += Kyf37KeypadIME Kyf37Home Kyf37OuterScreen libxml2
PRODUCT_PROPERTY_OVERRIDES += ro.sf.lcd_density=240 ro.kyf37.keypad_navigation=true ro.kyf37.outer_screen=true ro.kyf37.color_variation=3 ro.config.low_ram=true
PRODUCT_COPY_FILES += \
    """+' \
    '.join(copy)+'\n'+'# KYF37 OEM audio takes precedence over inherited AOSP audio\nPRODUCT_COPY_FILES := '+' '.join(sound_copy)+' $(PRODUCT_COPY_FILES)\n')
product=d/'lineage.mk'
product.write_text(product.read_text()+'\n# KYF37 OEM audio takes precedence over inherited AOSP audio\nPRODUCT_COPY_FILES := '+' '.join(sound_copy)+' $(PRODUCT_COPY_FILES)\n')
if args.oreo or args.android10:
 p=d/'device.mk'
 s=p.read_text().replace('$(call inherit-product, frameworks/native/build/phone-xhdpi-1024-dalvik-heap.mk)',
  'PRODUCT_PROPERTY_OVERRIDES += dalvik.vm.heapstartsize=8m dalvik.vm.heaptargetutilization=0.75 dalvik.vm.heapminfree=512k dalvik.vm.heapmaxfree=8m')
 s=s.replace(' ro.config.low_ram=true','')
 p.write_text(s)
# Candidate stock vendor closure, with provenance. ABI validation still required.
v=tree/'vendor/kyocera/kyf37';(v/'proprietary').mkdir(parents=True,exist_ok=True)
r=json.loads((host/'kyf37-rom/stock-native-dependencies.json').read_text());entries=r['proprietary_dependency_candidates']
# Keep model-specific HALs. AOSP supplies generic default implementations.
exclude={'lib/hw/audio.primary.default.so','lib/hw/audio.a2dp.default.so','lib/hw/audio.r_submix.default.so','lib/hw/audio.usb.default.so','lib/hw/audio_policy.default.so','lib/hw/gralloc.default.so','lib/hw/power.default.so','lib/hw/keystore.default.so','lib/hw/local_time.default.so','lib/hw/vibrator.default.so'}
# Never downgrade Android platform daemons/libraries to the stock 5.1 versions.
# Vendor HALs remain model-specific; their target-platform ABI must be validated.
exclude.update({'bin/rild','bin/wcnss_service','lib/egl/libGLES_android.so',
 'lib/libETC1.so','lib/libaudioroute.so','lib/libaudioutils.so',
 'lib/libcommon_time_client.so','lib/libft2.so','lib/libkeystore_binder.so',
 'lib/libnbaio.so','lib/libpixelflinger.so','lib/libpower.so','lib/libril.so',
 'lib/librilutils.so','lib/libskia.so','lib/libsoftkeymaster.so',
 'lib/libspeexresampler.so','lib/libtinyalsa.so','lib/libtinycompress.so',
 'lib/libsqlite.so','lib/libxml2.so','lib/hw/bluetooth.default.so'})
entries=[x for x in entries if x not in exclude]
# Removed from Android7 platform, but required by proprietary Adreno/network
# components. Its dependencies are libc, libm and the platform libstdc++ shim.
entries.append('lib/libstlport.so')
for p in (stock/'etc/wifi').glob('*'):
 if p.is_file():entries.append(str(p.relative_to(stock)))
support=json.loads((host/'kyf37-rom/hardware-support-files.json').read_text())
entries.extend(x['path'] for x in support['files'])
# Image construction must retain firmware links into writable calibration stores.
# Copying their targets would freeze per-device data into the ROM or omit wlan.ko.
link_rules=['LOCAL_PATH := $(call my-dir)', '']
for link in support['symlinks']:
 rel=link['path'];target=link['target']
 if not rel.startswith(('etc/firmware/','lib/modules/')) or '..' in rel.split('/'):
  raise ValueError('Unexpected hardware link path: '+rel)
 dest='$(TARGET_OUT)/'+rel
 link_rules.extend([dest+':', '\t@mkdir -p $(dir $@)',
                    '\t@ln -sfn '+target+' $@',
                    'ALL_DEFAULT_INSTALLED_MODULES += '+dest, ''])
(d/'Android.mk').write_text('\n'.join(link_rules)+'\n')
for rel in entries:
 p=v/'proprietary'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stock/rel,p)
 if rel=='vendor/lib/libOmxIttiamVdec.so':
  manifest=json.loads((host/'kyf37-rom/patched-vendor/ittiam-mapper-patch.json').read_text())
  import hashlib
  patched=host/'kyf37-rom/patched-vendor/libOmxIttiamVdec.so'
  assert hashlib.sha256((stock/rel).read_bytes()).hexdigest()==manifest['original_sha256']
  assert hashlib.sha256(patched.read_bytes()).hexdigest()==manifest['patched_sha256']
  shutil.copy2(patched,p)
(v/'kyf37-vendor.mk').write_text('PRODUCT_COPY_FILES += \
    '+' \
    '.join('vendor/kyocera/kyf37/proprietary/'+x+':system/'+x for x in sorted(set(entries)))+'\n')
(v/'proprietary-files.txt').write_text('\n'.join(sorted(set(entries)))+'\n')
shutil.copytree(d,host/('kyf37-rom/device-android10' if args.android10 else 'kyf37-rom/device-oreo' if args.oreo else 'kyf37-rom/device'),dirs_exist_ok=True)
shutil.copy2(v/'proprietary-files.txt',host/'kyf37-rom/proprietary-files-candidate.txt')
print('Created KYF37 product/device and candidate vendor tree:',len(entries),'stock files')
