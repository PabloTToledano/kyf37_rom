"""Package the opt-in full legacy ramdisk; no device access or signing."""
from pathlib import Path
import subprocess, tempfile, shutil, struct, gzip, hashlib, json, argparse
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=Path('/home/pablo/kyf37-rom/boot-android10-legacy-unsigned.img'))
parser.add_argument('--diagnostic',action='store_true')
parser.add_argument('--release',action='store_true')
parser.add_argument('--trial-seconds',type=int,choices=(120,600),default=120)
args=parser.parse_args()
tree=Path('/home/pablo/kyf37-android10')
product=tree/'out/target/product/kyf37'
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0, 'Build still active'
source=product/'boot.img'
output=args.output
assert not output.exists(), 'Choose a new artifact rather than overwrite'
data=source.read_bytes();assert data[:8]==b'ANDROID!'
fields=struct.unpack_from('<10I',data,8);page=fields[7]
assert page==2048 and fields[8]>2 # Legacy QCDT field, not a v1/v2 header.
pos=page;blobs=[]
for size in [fields[0],fields[2],fields[4],fields[8]]:
    blobs.append(data[pos:pos+size]);assert len(blobs[-1])==size
    pos+=(size+page-1)//page*page
with tempfile.TemporaryDirectory(prefix='kyf37-legacy-ramdisk-',dir='/home/pablo/kyf37-rom') as temp:
    root=Path(temp)/'root'
    shutil.copytree(product/'root',root,symlinks=True)
    init=root/'init';assert init.is_symlink()
    init.unlink()
    shutil.copy2(product/'ramdisk/init',init)
    assert init.read_bytes()[:4]==b'\x7fELF'
    # Verify patched early init is actually present, not just its source file.
    assert b'/fstab.kyf37.first_stage' in init.read_bytes()
    if args.diagnostic or args.release:
        assert b'/kyf37-init-debug' in init.read_bytes()
        if not args.release: (root/'kyf37-init-debug').write_text('Opt-in cache logging and next-boot recovery guard.\n')
        if not args.release: (root/'kyf37-debug').mkdir(mode=0o700,exist_ok=True)
        # Use authenticated ADB for this explicitly requested diagnostic trial.
        # Existing /data/misc/adb/adb_keys remain authoritative; no auth bypass.
        default=root/'default.prop'
        props=default.read_text()
        assert 'ro.adb.secure=1' in props and 'ro.debuggable=1' in props
        props=props.replace('persist.sys.usb.config=none','persist.sys.usb.config=adb')
        props=props.replace('ro.adb.secure=1','ro.adb.secure=0')  # owner: any computer, no auth dialog
        if 'persist.sys.root_access' not in props:
            props=props.rstrip('\n')+'\npersist.sys.root_access=3\n'  # Lineage: root for apps and adb; reset to 0 after a data reset otherwise ('adb root' refused)
        default.write_text(props)
        debug_rc=root/'init.kyf37.diagnostic.rc'
        debug_rc.write_text('on post-fs-data\n    setprop sys.usb.configfs 0\n    setprop persist.sys.usb.config adb\n    setprop sys.usb.config adb\n\non boot\n    setprop sys.usb.configfs 0\n    setprop persist.sys.usb.config adb\n    setprop sys.usb.config adb\n')
        debug_rc.write_text(debug_rc.read_text().replace('on post-fs-data\n', 'on post-fs-data\n    setprop persist.adb.nonblocking_ffs false\n    setprop sys.usb.ffs.aio_compat true\n', 1))
        if not args.release: debug_rc.write_text(debug_rc.read_text()+'\non post-fs-data\n    start kyf37-logcat\n\nservice kyf37-logcat /system/bin/logcat -b all -v threadtime -f /kyf37-debug/kyf37-logcat.txt -r 1024 -n 4\n    class core\n    user root\n    group root log readproc\n    seclabel u:r:logd:s0\n    disabled\n')
        if not args.release: debug_rc.write_text(debug_rc.read_text()+f'\non post-fs-data\n    start kyf37-trial-return\n\nservice kyf37-trial-return /system/bin/sh -c "sleep {args.trial_seconds}; setprop sys.powerctl reboot,recovery"\n    class core\n    user root\n    group root\n    seclabel u:r:init:s0\n    disabled\n    oneshot\n')
        debug_rc.write_text(debug_rc.read_text()+'\non post-fs-data\n    setprop dalvik.vm.usejit true\n    setprop dalvik.vm.usejitprofiles true\n')
        # The legacy gadget must be enabled after adbd binds FunctionFS endpoints.
        debug_rc.write_text(debug_rc.read_text()+'\non property:sys.usb.ffs.ready=1 && property:sys.usb.config=adb\n    write /sys/class/android_usb/android0/enable 0\n    write /sys/class/android_usb/android0/iSerial ${ro.serialno}\n    write /sys/class/android_usb/android0/functions adb\n    write /sys/class/android_usb/android0/enable 1\n    setprop sys.usb.state adb\n')
        status=root/'kyf37-state.sh'
        status.write_text('#!/system/bin/sh\nfor delay in 20 40 40; do\n sleep "$delay"\n {\n date\n for prop in ro.build.version.release sys.boot_completed sys.usb.config sys.usb.state sys.usb.configfs sys.usb.ffs.ready init.svc.adbd init.svc.audioserver init.svc.surfaceflinger; do echo "$prop=$(getprop $prop)"; done\n for node in enable functions state idVendor idProduct f_ffs/aliases; do echo "USB $node:"; cat /sys/class/android_usb/android0/$node; done\n ls -l /dev/usb-ffs/adb\n mount | grep firmware\n cat /proc/asound/cards\n ps -A\n } >> /kyf37-debug/kyf37-state.txt 2>&1\ndone\n')
        status.chmod(0o755)
        if not args.release: debug_rc.write_text(debug_rc.read_text()+'\non post-fs-data\n    start kyf37-state\n\nservice kyf37-state /system/bin/sh /kyf37-state.sh\n    class core\n    user root\n    group root\n    seclabel u:r:init:s0\n    disabled\n    oneshot\n')
        init_rc=root/'init.rc'
        init_rc.write_text(init_rc.read_text()+'\nimport /init.kyf37.diagnostic.rc\n')

    rows=[line for line in (root/'fstab.qcom').read_text().splitlines() if not line.lstrip().startswith('#') and len(line.split())>=5 and line.split()[1]=='/system']
    assert len(rows)==1
    columns=rows[0].split();assert columns[0]=='/dev/block/bootdevice/by-name/system' and columns[2]=='ext4'
    columns[4]='wait,first_stage_mount'
    (root/'fstab.kyf37.first_stage').write_text(' '.join(columns)+'\n')
    # The signed outer-screen app shares the system UID, but not graphics GID.
    # ueventd resolves the last matching permission rule; preserve graphics access.
    ueventd=root/'ueventd.qcom.rc'
    permission='/dev/graphics/fb1 0660 system graphics\n'
    if permission not in ueventd.read_text():
        ueventd.write_text(ueventd.read_text()+'\n# System-UID outer-screen renderer.\n'+permission)
    assert (root/'init.rc').is_file() and (root/'sepolicy').is_file()
    archive=subprocess.check_output([str(tree/'out/host/linux-x86/bin/mkbootfs'),'-d',str(product/'system'),str(root)])
    blobs[1]=gzip.compress(archive,compresslevel=9,mtime=0)
header=bytearray(data[:page]);struct.pack_into('<I',header,16,len(blobs[1]))
sha=hashlib.sha1()
for blob in blobs:
    sha.update(blob);sha.update(struct.pack('<I',len(blob)))
header[576:608]=sha.digest()+bytes(12)
result=bytes(header)+b''.join(blob+bytes((-len(blob))%page) for blob in blobs)
assert len(result)<=16777216
output.write_bytes(result)
report={'source':str(source),'output':str(output),'bytes':len(result),'sha256':hashlib.sha256(result).hexdigest(),'full_legacy_ramdisk':True,'early_mount':'system only; retained rootfs, no pivot into legacy /system','owner_signed':False,'hardware_boot_verified':False}
Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/android10-legacy-boot-packaging.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
