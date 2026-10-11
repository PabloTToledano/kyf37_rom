# KYF37 Android 10 — project guide

Updated 2026-10-11. This is the current-state entry point; `docs/README.md` indexes everything else. Dated history lives in `docs/history/`, `docs/releases/` and `docs/CHANGELOG-2026-10-11.md`; a pre-reorganisation copy of this file is in `archive/KYF37-PROJECT-before-reorg-20261011.md`.

## 1. The device

Kyocera GRATINA KYF37 flip phone: MSM8909 / Adreno 304, 32-bit Cortex-A7, about 1 GB RAM (low-RAM config, ART JIT, 384 MB zram), 480×854 non-touch panel, D-pad and keypad, 128×36 monochrome outer screen. Running a custom **Android 10 Go (LineageOS 17.1, QQ3A.200805.001)** on the OEM Linux 3.10.49 kernel. ADB serial `981108631314`. Recovery: owner-signed TWRP 3.7.0_9-0 with the keitai D-pad UI.

Physical keys (scan code → role): Contacts/F1 top-left (59), Camera/F2 top-right (60), Email/F3 bottom-left (61), Browser/F4 bottom-right (62), OK in the centre, Clear/Back (355), Call (231), side key (254, side clock/shade). Quick-launch corners act only on Home; other apps receive the keys.

## 2. Rules that never change

- Never write recovery, keystore, modem/persist/NV partitions; never wipe userdata. Keep `phone-backup/`, `kyf37-twrp-device/`, `device-inspection/system-stock.img`, stock images and the SD rollback folders.
- The owner signing key (`kyf37-twrp-device/owner-signing-key.pem`) is never printed, copied, hashed or uploaded; use `device-inspection/sign-rom-boot.py`.
- Never flash the original stock ROM; only the custom Android 10 ROM.
- The agent never enters or guesses the SIM PIN; the owner types it.
- One build tree and one phone are shared: builds only through `device-inspection/build-locked.sh`; any phone mutation or reboot only while holding `tools/phone-lock.ps1` (`status`, `acquire <name> <min>`, `release`). **Check the lock and the other agent's logs before any `adb reboot`** (a release flash was disturbed on 2026-10-11 by reboots made without checking).
- Every source change is an idempotent script (`device-inspection/fix-android10-*.py`, `stage-*`, `port-*`) so the tree can be rebuilt from scratch. Running an older generator after a newer one can undo it; the wrapper `device-inspection/build-kyf37-android10.sh` defines the order.
- Signature|privileged permissions in a priv-app need a privapp allowlist or system_server crash-loops at boot.
- Git Bash mangles `/system/...` paths: set `MSYS_NO_PATHCONV=1` or use PowerShell.

## 3. Current state (2026-10-11)

- **Release v23** (keypad system UI, contextual corner-key guides, Home redesign, outer screen v2 sources) was packaged and installed from TWRP (`kyf37-rom/kyf37-android10-go-20261007-twrp-v23-keypad.zip`, SHA-256 `473c86ce…b102c`; notes `docs/releases/RELEASE-v23.md`; flash logs `kyf37-rom/v23-*.log`). The v23 install was interrupted and resumed once; later hardware checks are partial.
- v22 (`…-twrp-v22.zip`) is kept as the rollback release; v19/v20 are in `archive/releases/`.
- Workspace is reorganised: see section 4.

### Works (hardware-verified at some point)

### Not verified or open

## 4. Workspace map

| Path | What it is |
|---|---|
| `AGENTS.md` | Short entry point for any agent; points here |
| `KYF37-PROJECT.md` | This guide |
| `docs/` | `README.md` index; `FIXES.md` (root causes + scripts); `ui/`, `radio/`, `hardware/`, `kernel/`, `recovery/`, `releases/`, `history/`; `CHANGELOG-2026-10-11.md` |
| `kyf37-rom/` | Release candidates (v22, v23), installer ZIPs, validation JSON, release logs, ported-app artifact folders, current live APKs |
| `archive/` | Superseded releases, old audit reports, screenshots, recovery dumps, stray research binaries; every move recorded in `archive/MANIFEST-20261011.tsv` (undo: `python tools/tidy-workspace.py --undo`) |
| `phone-backup/`, `kyf37-twrp-device/` | Stock backups and recovery tooling incl. the owner key. Do not touch |
| `radio-work/`, `modem-investigation/`, `kernel-port-research/` | Radio/modem logs and tools, kernel research data |
| `tools/` | PowerShell/Python helpers: `phone-lock.ps1`, `flash-release.ps1`, `enter-twrp.ps1`, `keitai-recovery.ps1`, `outer-shot.py`, `survey-clutter.py`, `tidy-workspace.py`, scrcpy |

WSL (Ubuntu): Android source `~/kyf37-android10` (`lunch lineage_kyf37-userdebug`), kernel `~/kyf37-rom/kernel-android10` (GCC 4.8 only), stock system `~/kyf37-rom/stock-system`. Windows adb: `C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe`.

## 5. Build, package, flash

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-locked.sh /home/pablo/vNN-build.log   # require BUILD_EXIT=0
wsl -d Ubuntu -- bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/package-release.sh vNN
python device-inspection/sign-rom-boot.py <candidate>/boot-android10-unsigned.img <candidate>/boot-android10-owner-signed.img
python device-inspection/build-twrp-android10-installer.py vNN
```

- A single app: `build-locked.sh <log> <Module>` (for example `Kyf37Home`), sign with `device-inspection/sign-test-apk.sh in.apk out.apk`, then `adb install -r -d`. Priv-app changes that must survive: `device-inspection/deploy-outer-live.sh` shows the pattern (clear system write-protect, replace the APK and lib, reboot).
- Release boot only (never `--diagnostic`); kernel and out-of-tree modules (`pronto_wlan.ko`, `core_ctl.ko`) must come from the same build (`build-kyf37-modules.sh`); the gate `check-release-image.py` runs inside `package-release.sh`.
- Never install isolated framework/services/SystemUI changes on a running phone; use a matching validated image set.
- Flash only with the exclusive phone lock, via `tools/flash-release.ps1` from TWRP. It saves boot/system rollback images on the SD (needs about 1.7 GB free). After the first boot require `sys.boot_completed=1`, expected focused window, no new FATAL EXCEPTION and over 15 minutes uptime.
- If the phone lands in recovery after a reboot, clear misc bytes 0–31 and reboot (`dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1 count=32 conv=notrunc`).

## 6. Where the knowledge is

`docs/README.md` is the index. In short:

- Root causes and how to reproduce each fix: `docs/FIXES.md`.
- Keypad UI, themes, outer screen: `docs/ui/`. Radio/modem/RIL: `docs/radio/`. Camera, GPU, microG, FeliCa, TV, root: `docs/hardware/`. Kernel research: `docs/kernel/`.
- Bricked phone: `docs/recovery/USB-RECOVERY.md`; recovery images and tooling: `docs/recovery/`.
- Release notes per version: `docs/releases/`. Older hand-offs and status notes: `docs/history/` (byte-exact originals also in `kyf37-rom/documentation-history-20261011.zip`).
- Component evidence stays next to the artifacts: `kyf37-rom/all-stock-app-ports/`, `device-inspection/outer-animation/`, `device-inspection/keypad-ui-validation/`.

## 7. Publishing

The public repository is https://github.com/PabloTToledano/kyf37_rom: text sources and docs only. The ROM zip and the recovery image are GitHub Release assets (tag `v23`). To refresh it:

1. `python tools/export-repo.py --dest C:/Users/pablo/Documents/ChatGPT/kyf37_rom_stage` — whitelist copy with IMEI / Wi-Fi name / MAC redaction. It never copies keys, images, APKs, backups or logs.
2. In WSL copy the stage into a clone of the repo (`rsync -a --delete --exclude=.git`), review `git diff`, commit as PabloTToledano (GitHub noreply address, no co-author trailer) and push.
3. Never commit anything under `phone-backup/`, `archive/`, `kyf37-twrp-device/owner-signing-key.pem`, or firmware, blobs and APKs.
