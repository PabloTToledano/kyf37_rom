#!/bin/bash
# Stage the static qemu-arm (apt-get download qemu-user; dpkg -x into ~/qemu-dl/root) inside the hosttest chroot.
set -e
T=/home/pablo/kyf37-twrp-hosttest/root
Q=/home/pablo/qemu-dl/root/usr/bin/qemu-arm
if [ ! -x $Q ]; then
  mkdir -p ~/qemu-dl && cd ~/qemu-dl && apt-get download qemu-user && dpkg -x qemu-user_*.deb root
fi
mkdir -p $T/qemu $T/dev/input $T/dev/graphics $T/proc $T/tmp $T/sys
cp -f $Q $T/qemu/qemu-arm
echo staged
