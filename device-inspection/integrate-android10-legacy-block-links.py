"""Restore the KYF37's legacy bootdevice links during first-stage init.

Opt-in only through the existing KYF37 full-root first-stage fstab marker.
The Android 10 generic DeviceHandler otherwise never creates these links.
"""
from pathlib import Path
import subprocess,json
tree=Path('/home/pablo/kyf37-android10')
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode!=0
fstab=tree/'system/core/fs_mgr/fs_mgr_fstab.cpp'
source=fstab.read_text()
patch='''    // KYF37 legacy rootfs uses androidboot.bootdevice (singular), not
    // Android 10's boot_devices list. Limit compatibility to its opt-in ramdisk.
    if (access("/fstab.kyf37.first_stage", F_OK) == 0 &&
        fs_mgr_get_boot_config_from_kernel_cmdline("bootdevice", &value) && !value.empty()) {
        return {value};
    }

'''
if patch not in source:
    anchor='    // Fallback to extract boot devices from fstab.\n'
    assert source.count(anchor)==1
    fstab.write_text(source.replace(anchor,patch+anchor,1))
devices=tree/'system/core/init/devices.cpp'
source=devices.read_text()
patch='''    // Opt-in KYF37 first-stage mount requires the stock bootdevice links.
    // The legacy command line names the controller without its soc parent.
    const bool kyf37_legacy_links = access("/fstab.kyf37.first_stage", F_OK) == 0;
    if (kyf37_legacy_links && !is_boot_device) {
        const auto slash = device.rfind('/');
        const auto controller = device.substr(slash == std::string::npos ? 0 : slash + 1);
        is_boot_device = boot_devices_.find(controller) != boot_devices_.end();
    }
'''
if patch not in source:
    anchor='    bool is_boot_device = boot_devices_.find(device) != boot_devices_.end();\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+patch,1)
    anchor='            links.emplace_back("/dev/block/by-name/" + partition_name_sanitized);\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+'''            if (kyf37_legacy_links) {
                links.emplace_back("/dev/block/bootdevice/by-name/" + partition_name_sanitized);
            }
''',1)
    devices.write_text(source)
board=tree/'device/kyocera/kyf37/BoardConfig.mk'
source=board.read_text()
target='androidboot.init_fatal_reboot_target=recovery'
if target not in source:
    line=next(line for line in source.splitlines() if line.startswith('BOARD_KERNEL_CMDLINE := '))
    board.write_text(source.replace(line,line+' '+target,1))
report={'problem':'First-stage fstab requires bootdevice/by-name/system, but Android 10 DeviceHandler never creates bootdevice links and GetBootDevices ignores singular androidboot.bootdevice',
        'fix':'KYF37 marker-gated singular bootdevice fallback, controller basename match and legacy per-partition links',
        'early_init_fatal_target':'recovery','observed_bootloop_cause_confirmed':False,'hardware_tested':False}
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
(root/'kyf37-rom/android10-legacy-block-links.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
