from pathlib import Path
p=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/device.mk');s=p.read_text();s=s.replace('$(TARGET_OUT_VENDOR)/','out/target/product/kyf37/system/vendor/');p.write_text(s)
# Supply a real declared firmware label for the OEM read-only modem mount.
policy=p.parent/'sepolicy/kyf37_firmware.te'
policy.write_text('type kyf37_firmware_file, file_type, vendor_file_type;\nr_dir_file(ueventd, kyf37_firmware_file)\n')
fc=p.parent/'sepolicy/file_contexts';s=fc.read_text();s+='\n/firmware(/.*)? u:object_r:kyf37_firmware_file:s0\n';fc.write_text(s)
rc=p.parent/'ramdisk/init.target.rc';s=rc.read_text();assert 'context=u:object_r:firmware_file:s0' in s;s=s.replace('context=u:object_r:firmware_file:s0','context=u:object_r:kyf37_firmware_file:s0');rc.write_text(s)
print('Display provider paths made concrete; firmware mount gets declared SELinux label')
