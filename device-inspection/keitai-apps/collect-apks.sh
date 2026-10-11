#!/bin/bash
set -x
D=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/keitai-apps
P=$HOME/kyf37-android10/out/target/product/kyf37/system/app
for a in Kyf37Dialer Kyf37Messages Kyf37Contacts; do cp $P/$a/$a.apk $D/ ; done
ls -la $D
