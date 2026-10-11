#!/bin/bash
set -euo pipefail
task_root=/home/pablo/kyf37-twrp
mkdir -p "$task_root" /home/pablo/.local/bin
if [ ! -f /home/pablo/.local/bin/repo ]; then
  curl -fL https://storage.googleapis.com/git-repo-downloads/repo -o /home/pablo/.local/bin/repo
  chmod 755 /home/pablo/.local/bin/repo
fi
export PATH=/home/pablo/.local/bin:$PATH
export GIT_AUTHOR_NAME='KYF37 local build'
export GIT_AUTHOR_EMAIL='kyf37@localhost'
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
cd "$task_root"
if [ ! -d .repo/manifests ]; then
  repo init -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_omni.git -b twrp-5.1 --depth=1 --no-clone-bundle
fi
repo sync -c -j4 --no-clone-bundle --no-tags
