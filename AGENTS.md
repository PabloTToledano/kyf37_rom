# KYF37 project entry point

1. Read `KYF37-PROJECT.md` (current state, rules, workspace map, build/flash). `docs/README.md` indexes the details.
2. Mandatory: no recovery/keystore/modem/persist/NV writes or userdata wipes. Never read, print, copy, hash or upload the owner signing private key. Preserve `phone-backup/`, `kyf37-twrp-device/`, `device-inspection/system-stock.img` and the SD rollback folders. Never flash the original stock ROM. Never enter the SIM PIN.
3. Builds only through `device-inspection/build-locked.sh`; phone mutations and reboots only under `tools/phone-lock.ps1` (check `status` and the other agent's logs first). Keep source edits in rerunnable fix scripts. Do not claim an unflashed release is hardware verified. Keep native authentication and the native default dialer.
