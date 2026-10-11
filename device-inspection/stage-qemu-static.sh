#!/bin/bash
# Fetch qemu-user-static (no root needed: apt-get download + dpkg -x) into ~/qemu-static
set -e
mkdir -p ~/qemu-static && cd ~/qemu-static
[ -x root/usr/bin/qemu-arm-static ] && { echo have; exit 0; }
apt-get download qemu-user-static >/dev/null 2>&1 || apt-get download qemu-user-static
dpkg -x qemu-user-static_*.deb root
ls -la root/usr/bin/qemu-arm-static
