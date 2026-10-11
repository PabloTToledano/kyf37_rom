# Agent briefing — KYF37 Android 10 ROM (read after AGENTS.md)

Two specialist agents work in parallel with the lead agent on the same phone and the same source tree.
Coordination rules are mandatory because there is **one phone** and **one build tree**.

## Roles

| Agent | Scope | Doc to write | Zip revision names |
|---|---|---|---|
| **lead** | integration, keypad/UI, microG, final TWRP zips | `AGENTS.md`, `KEYPAD.md`, `MICROG.md` | v14 – v19 |
| **radio** | Wi-Fi (WCNSS/prima) **and** cellular/LTE (modem, rild, QMI, IRadio HAL, SIM, data, calls, SMS) | `RADIO.md` | v20 – v29 |
| **tv** | One Seg TV: make the stock FsDtvApp + dtvserver native stack load and run on Android 10 (resolve the 62 unresolved symbols and the Binder/Skia/audio/graphics ABI gaps) | `TV.md` | v40 – v49 |
| **gpu** | Adreno 304 userspace/kernel (kgsl), SurfaceFlinger/HWC/MDP3 display path, tearing, performance & memory tuning | `GPU.md` | v30 – v39 |

## Hard rules (all agents)

1. **Never** delete or overwrite: `phone-backup/`, `device-inspection/system-stock.img`, the owner signing key (`kyf37-twrp-device/owner-signing-key.pem` — never print, copy or upload it), anything on the phone's `recovery`, `keystore`, modem/`persist`/`modemst*`/`fsg`/`dnand` partitions, or the SD card's TWRP backups, `kyf37-download-triggers-disabled`, and rollback folder `KYF37-Android10-rollback-19691231-191652-367` (it holds the **stock** boot+system).
2. **Builds:** never start `build-kyf37-android10.sh` directly. Use `wsl -d Ubuntu -- bash -c "cd ~ && (setsid nohup bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-locked.sh ~/<yourname>-build.log < /dev/null > /dev/null 2>&1 &)"`. It serialises builds with `flock`. Poll your log for `BUILD_EXIT=` / `build completed`. A broken build blocks everybody: compile-test small changes promptly and **revert your own change if it breaks the build**.
3. **Phone:** hold the cooperative lock while flashing, rebooting, or doing anything that changes device state for more than a minute: `powershell -File tools\phone-lock.ps1 acquire <name> 45` … `release <name>`. Read-only `adb shell` queries do not need it. Always release it when done or idle.
4. **Source edits:** make every change an idempotent script `device-inspection/fix-android10-<topic>.py` (WSL, Python 3) like the existing ones, so a tree can be rebuilt from scratch. Don't hand-edit the WSL tree without also scripting it. Don't rewrite other agents' scripts.
5. **Zips:** package with `device-inspection/package-release.sh <rev>` then sign + `build-twrp-android10-installer.py <rev>` (add your revision to the tuples in that script with `sed`; use only your own revision names from the table). Flash with `tools/flash-release.ps1 <zip>` (while holding the phone lock). Never flash an image that was not produced by that pipeline.
6. **Safety nets:** keep the phone recoverable. If TWRP loops, follow `AGENTS.md` section 4 (`fastcap.py`, `fsck-race.py`). If everything fails use `KYF37-USB-RECOVERY-RUNBOOK.md`. Do not change `boot` without the owner-signed pipeline.
7. **Honesty:** write what you verified on hardware vs what you only built. Note failed experiments in your doc (so nobody repeats them).
8. The owner does not want questions; make a reasonable decision and document it. Internet research is allowed (microg.org, github, postmarketOS wiki, LineageOS, CAF/CodeLinaro, XDA). Download only from reputable sources, record URL + SHA-256, never run downloaded binaries on the host, and keep third-party blobs in `third-party/<topic>/` with a README of provenance/licence.
9. MSYS path mangling: set `MSYS_NO_PATHCONV=1` in Git Bash or use PowerShell for adb paths. `/system` writes need `clear-system-temp-wp` first (AGENTS.md §4). After `adb root`, wait 4 s.
10. When you finish a milestone or run out of ideas, append a dated section to your doc and to `AGENTS.md §6` (status), then end with a concise report: what works, what doesn't, files changed, how to reproduce.

## Current baseline (lead updates this)

Phone runs TWRP-installed **v13** plus live patches (Cipo libs, Wi-Fi rc, privapp keypad xml). **v14** (all pending fixes + microG + new boot animation) is being built; wait for the "BASELINE v14" line below before flashing anything, and base your work on the tree as it is then.

BASELINE v15 (supersedes v14; adds Aurora Store): zip `kyf37-rom/kyf37-android10-go-20261007-twrp-v15.zip` (sha256 c6f6cfe4…0319) is built from the tree as of 2026-10-08 19:26 (includes microG, Wi-Fi supplicant rc, camera fixes, cpuset, ringtones, wallpaper, user boot animation, plus the gpu agent's uncached-fb and zram patches). The lead flashes it when the phone lock is free; check `tools\phone-lock.ps1 status` and `adb shell getprop ro.build.date` before assuming it is installed. System tree is ~1358 MB of 1538 MB: **the system partition is nearly full**; GmsCore was ABI-stripped to fit — check `du -sm out/target/product/kyf37/system` before adding big files.

## Hazards discovered by agents
* **Never read `/sys/kernel/debug/mdp/panel_reg`** on this MDP3 kernel: it panics the phone (gpu agent, 2026-10-08).
* After an unclean reboot, check `/data` with `fsck-race.py` if TWRP loops (AGENTS.md §4).
