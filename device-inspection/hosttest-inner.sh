#!/bin/bash
# runs inside `unshare -r -m -p -f` (fake root + private mount/pid namespaces)
T=/home/pablo/kyf37-twrp-hosttest/root
touch $T/dev/null $T/dev/zero $T/dev/urandom $T/dev/tty 2>/dev/null
for d in null zero urandom tty; do mount --bind /dev/$d $T/dev/$d 2>/dev/null; done
mount -t proc proc $T/proc 2>/dev/null
exec chroot $T /qemu/qemu-arm ${QEMU_EXTRA} /sbin/recovery
