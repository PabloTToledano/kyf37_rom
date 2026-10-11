#!/bin/bash
# usage: dump-manifest.sh Kyf37Dialer   -> aapt2 dump of the built APK manifest (permissions, components, filters)
R=$HOME/kyf37-android10
$R/out/host/linux-x86/bin/aapt2 dump xmltree --file AndroidManifest.xml $R/out/target/product/kyf37/system/app/$1/$1.apk
