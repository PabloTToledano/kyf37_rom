#!/bin/bash
# One-off continuation: waits for the already-started pinned download, then
# compares and builds. No existing tree writes and no device operations.
set -euo pipefail
root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research
work=/home/pablo/kyf37-kernel-port-research
trap 'rc=$?; printf "PIPELINE EXIT: %s at %s\n" "$rc" "$(date -Is)"; exit "$rc"' EXIT
printf 'PIPELINE START: %s\n' "$(date -Is)"
if [ -n "${1:-}" ]; then
    while kill -0 "$1" 2>/dev/null; do sleep 5; done
fi
gzip -t "$work/donor.tar.gz"
python3 "$root/unpack-donor.py"
python3 "$root/compare-kernels.py" "$work/kernel-3.18"
bash "$root/build-318.sh"
