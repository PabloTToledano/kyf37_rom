#!/bin/bash
set -euo pipefail
task_tools=/home/pablo/kyf37-host-tools
mkdir -p "$task_tools"
cd "$task_tools"
if [ ! -x python2/bin/python2.7 ]; then
  if [ ! -f Python-2.7.18.tgz ]; then
    curl -fL https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz -o Python-2.7.18.tgz
  fi
  tar -xzf Python-2.7.18.tgz
  cd Python-2.7.18
  CFLAGS='-O2 -std=gnu99' ./configure --prefix="$task_tools/python2" --without-ensurepip
  make -j4
  make install
  cd "$task_tools"
fi
if [ ! -x jdk8/bin/java ]; then
  curl -fL 'https://api.adoptium.net/v3/binary/latest/8/ga/linux/x64/jdk/hotspot/normal/eclipse' -o jdk8.tar.gz
  mkdir -p jdk8
  tar -xzf jdk8.tar.gz --strip-components=1 -C jdk8
fi
