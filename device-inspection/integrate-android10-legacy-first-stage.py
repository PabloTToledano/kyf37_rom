from pathlib import Path
import subprocess
if subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Build active')
p=Path('/home/pablo/kyf37-android10/system/core/init/first_stage_mount.cpp')
s=p.read_text()
old='static Fstab ReadFirstStageFstab() {\n    Fstab fstab;\n'
new=old+'''    // Opt-in legacy rootfs ramdisk. The separate early fstab mounts only system.
    // No userdata mount/format or partition-layout change occurs here.
    if (access("/fstab.kyf37.first_stage", F_OK) == 0) {
        if (!ReadFstabFromFile("/fstab.kyf37.first_stage", &fstab)) {
            LOG(FATAL) << "Cannot read KYF37 early-mount fstab";
        }
        return fstab;
    }
'''
if new not in s:
    assert old in s
    s=s.replace(old,new,1)
old='        SwitchRoot("/system");'
new='''        // This device retains /system as a mount beneath the packaged rootfs.
        // Its full init scripts and mount-point symlinks remain in the ramdisk.
        if (access("/fstab.kyf37.first_stage", F_OK) != 0) {
            SwitchRoot("/system");
        }'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new,1)
p.write_text(s)
print('Opt-in legacy /system early mount; rootfs retained and normal Android 10 SELinux/second-stage init unchanged.')
