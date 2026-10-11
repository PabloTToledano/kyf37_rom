# KYF37 root setup â€” verified 2026-10-06

Magisk 23 runtime root now starts automatically after a normal reboot through
the stock init `rootagent` service. `persist.sys.rootagent=1` enables the hook
at `/system/etc/init.qcom.rootagent.sh`. The script starts the Magisk daemon
from `/data/local/tmp/magisk` and binds the root tool directory over
`/system/xbin`. Do not delete the Magisk binary, `enable-app-root.sh`, or
`kyf37-root-xbin` under `/data/local/tmp` while using this setup.

Verified after reboot without running the host activation script:
- Android completed boot, the rootagent hook exited successfully.
- Ordinary ADB `su -c id` returned UID 0.
- A process running as the Magisk app UID 10116 requested `su` and received UID 0.

Evidence: `persistent-root-reboot-verification.txt` and
`persistent-app-root-verification.txt`.

SELinux remains permissive through the previously enabled diagnostic factory
flag. This setup depends on that mode. Root authorization is managed by the
installed Magisk app. Shell UID 2000 has an explicit permanent allow policy.

To disable automatic startup, run `adb shell 'su -c "setprop persist.sys.rootagent 0"'`
and reboot. To re-enable runtime access from the computer, use the existing
`Enable-SessionRoot.ps1`. A factory reset removes the data-side binaries and
breaks this startup arrangement; it is not a boot image installation.

The failed earlier system writes were blocked by eMMC temporary write
protection. A read-only CMD31 query found the system groups protected. The
live system hash still equalled the pre-change backup. A narrowly scoped CMD29
helper cleared temporary protection for groups intersecting system; it did
not modify permanent write-protection settings. The startup script then
persisted through sync and reboot. The shared first 4 MiB group also overlaps
the preceding partition; no other partition contents were written.

Do not attempt further system writes without checking write protection first.
The original full eMMC backup and stock boot/recovery images are preserved in
`phone-backup`. The bootloader remains locked. Since this root setup, owner-signed stock boot and a custom TWRP recovery have been flashed using the user-keystore verification path. See ../kyf37-twrp-device/README.md for controls, signing, and rollback requirements.
