# Current status: performance and battery candidate

Complete consolidated handoff: [HANDOFF-KERNEL-PERFORMANCE.md](C:/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research/HANDOFF-KERNEL-PERFORMANCE.md). It covers research, completed changes, discoveries/failures, evidence, exact artifact paths/hashes, reproduction and the unexecuted battery-measurement plan. This is the entry point for continuing the work; physical-phone access remains prohibited.

2026-10-08: the additional performance work is built and host-validated in `performance-candidate/`. It adds stable 4.1 zsmalloc packing/compaction with a tested no-progress guard, stable 3.18 power-efficient disk-event workqueues, interactive default CPU scaling and a balanced one-shot post-boot policy. The policy removes the vendor 800 MHz floor, permits one core at light load, changes the low-frequency target load from 1 to 85 and bounds eMMC readahead at 128 KiB. It preserves maximum frequency, thermal protection and automatic hotplug.

See `performance-candidate/README.md`, the full source patch, unsigned boot images and JSON evidence. The previous candidate artifacts retain their original hashes. The independent WSL source/build workspace now includes these extra changes; use `build-performance.sh` and the performance verification/packaging scripts to reproduce them. The original working kernel's 47,017 snapshotted files remain unchanged. No physical-phone access, signing or installation occurred; real speed, suspend and battery results remain unmeasured.

## Previous completed candidate

2026-10-08: implementation, host builds, ARM component tests, module checks and unsigned candidate packaging are complete. See `backports-candidate/README.md` and its verification reports. Selected features are MemAvailable, getrandom, newer zram with LZ4/multiple streams/limits/statistics and an optional bounded zram policy. Existing ROM/kernel folders remain unchanged.

Physical-phone access/testing is prohibited by the latest owner instruction. No phone access occurred after it; nothing was signed, installed or flashed. Hardware behavior and performance remain unverified.

The prior 3.18 pipeline was stopped when the objective changed. Its source archive transfer ended with curl error 18 and is incomplete; it was never used for a build. Backports use complete, individually fetched, pinned upstream reference files. No background kernel job remains.

Independent backport workspace: `/home/pablo/kyf37-kernel-port-research/backports`. Latest build: `logs/backports-build.log`.

## Historical full-3.18-port notes (superseded)

Started 2026-10-08 at the owner's request to implement the port.

Current milestone: donor acquisition and initial board/config translation.
No compiled or hardware-tested newer kernel exists yet.

- Pinned donor: `saga0324/android_kernel_kyocera_afp`, branch `902/3/4KC`, commit `652b4259bd6f6195beda2e55c0b36a090257bcd8`.
- Downloaded donor defconfig confirms MSM8909, MDP3, WCNSS, fb1 extensions, 32-bit Binder and memory/seccomp support.
- Original KYF37 EVT/DVT DT include closure was checked: 28 files. It includes a shared skeleton outside qcom, which the isolated copy now preserves.
- `prepare-kyf37-318.py` translates the effective current kernel config against the donor's declared symbols and copies the board include closure into a dedicated donor subtree. It reports missing baseline symbols. The legacy bindings need review against donor drivers; this is initial translation, not complete hardware enablement.
- `compare-kernels.py` inventories driver and UAPI differences before changes.
- `build-318.sh` uses the available GCC 4.8 toolchain and builds zImage, modules and DTBs into a NEW output directory.
- Python syntax for the initial preparation/comparison scripts and shell syntax for build/continuation were checked. Full preparation and compilation await the source archive.

## Running work

The pinned archive is downloading into `/home/pablo/kyf37-kernel-port-research/donor.tar.gz` (PID 32575 at launch). Acquisition was slow, roughly tens of KB/s. Earlier Windows-folder transfer attempts were stopped; partial files are not usable source archives.

A one-off continuation (PID 32643 at launch; see `logs/pipeline.pid`) waits for that download, verifies gzip/archive structure, extracts into `/home/pablo/kyf37-kernel-port-research/kernel-3.18`, records provenance, compares sources, prepares the port, and attempts the first build. Log: `logs/port-build.log`. A failed stage stops the pipeline. No flash or ROM staging is included.

Build output: `/home/pablo/kyf37-kernel-port-research/build-3.18`.
All WSL writes belong to this new experimental directory. Existing `/home/pablo/kyf37-rom` and `/home/pablo/kyf37-android10` are read only. All Windows writes belong to this `kernel-port-research` folder. No signing key was accessed or copied, and no phone operations were performed.

## Next continuation

Read `logs/port-build.log` and inspect the running PIDs before starting anything again. If the build fails, make repeatable fixes inside this experiment and rebuild. If it succeeds, review effective config differences, legacy DT bindings and vendor ioctl ABI differences before packaging anything. A donor compile alone is not a KYF37 boot proof. Do not flash a 902KC board DT or reuse old 3.10 modules.

The assessment's multi-month estimates describe human effort, not a reason to stop implementation. The next required evidence is an actual isolated build followed by reviewed board/ABI compatibility and a controlled hardware test.
