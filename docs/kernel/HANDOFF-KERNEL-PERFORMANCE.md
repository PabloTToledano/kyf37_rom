# KYF37 kernel research, backports and performance handoff

Updated: 2026-10-08. This document consolidates the work and findings from this conversation. It is the current entry point; `ASSESSMENT.md` and the older sections of `STATUS.md` describe earlier stages.

## 1. Result and owner constraints

The delivered result is a **compiled, unsigned, uninstalled Linux 3.10.49 candidate** with selected newer-kernel features and a separate balanced performance/battery boot policy. This is not a completed port to Linux 3.18 or 4.1. Only selected subsystems were backported.

Main Windows result directory:

`C:\Users\pablo\Documents\ChatGPT\flipphone_roms\kernel-port-research\performance-candidate`

Main boot image:

`C:\Users\pablo\Documents\ChatGPT\flipphone_roms\kernel-port-research\performance-candidate\boot-performance-balanced-unsigned.img`

Candidate overview: [performance-candidate/README.md](C:/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research/performance-candidate/README.md). Verification: [performance-candidate/final-audit.json](C:/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research/performance-candidate/final-audit.json). Integrity: [performance-candidate/SHA256SUMS](C:/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research/performance-candidate/SHA256SUMS).

The owner requested a new folder and preservation of the existing ROM/kernel work. All implementation writes were confined to `kernel-port-research` on Windows and `/home/pablo/kyf37-kernel-port-research` in WSL. The source-preservation audit verified 47,017 snapshotted original kernel files. The previous backport candidate's recorded file hashes also remained unchanged.

**The owner's latest instruction forbids physical-phone testing.** No phone access occurred after that instruction. Earlier read-only baseline inspection must not be confused with testing or validation of these new candidates. Nothing was flashed, installed, signed or rebooted as part of the candidate work. The owner signing key was not accessed, printed, copied or uploaded.

Continue to preserve recovery, keystore, modem/persist/NV, userdata and stock rollback. This document does not authorize device access or deployment. The older project instruction to verify on hardware is superseded by the owner's explicit no-phone instruction.

## 2. Device and original-kernel findings

The project targets Kyocera GRATINA KYF37: MSM8909, 32-bit ARM Cortex-A7, approximately 1 GB RAM, eMMC, a 480x854 non-touch main panel, keypad/lid controls and a 128x36 visible outer display. The ROM is Android 10/LineageOS 17.1 over an OEM Linux 3.10.49 base.

Original reference paths, used read-only:

| Input | Location |
|---|---|
| Kernel source | WSL `/home/pablo/kyf37-rom/kernel-android10` |
| Original effective build configuration | WSL `/home/pablo/kyf37-rom/kernel-android10-gcc48-build/.config` |
| Android source | WSL `/home/pablo/kyf37-android10` |
| Vendor modules and post-boot script | WSL `/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary` |
| Release boot used for packaging | Windows `kyf37-rom/android10-go-candidate-20261007-v13/boot-android10-unsigned.img` |

Important findings:

- The original source had substantial existing local Android compatibility changes. At the initial inspection, HEAD was `57a11bec679273e797cbf3fcb3fc1488637b3fe6`; its tracked diff contained 41 files, 2,555 insertions and 527 deletions. A clean clone of that commit would omit those changes and any untracked additions. The independent baseline therefore snapshots the working files, rather than assuming Git HEAD is the working kernel.
- The existing integration depends on legacy Qualcomm/Kyocera MDP3, KGSL/ION, SMD/modem/audio, WCNSS/Pronto, power and OEM outer-display interfaces. Replacing the kernel version alone does not make the proprietary userspace compatible.
- GCC 4.8 is the established compiler for this source. The project records failed GCC 4.9 experiments, but their exact failure mechanism was not established here.
- Boot capacity is 16 MiB. OEM DT selection, legacy boot geometry, early init and SELinux policy support must survive packaging.
- Existing vendor modules use versioned symbols. Both release/vermagic and actual symbol CRCs matter; matching the text `3.10.49` alone is insufficient.
- Tickless idle, CPU idle, runtime power management, seccomp filtering and pstore/ramoops support were already enabled. These did not need to be newly added.
- TASKSTATS is disabled in the delivered configuration. PSI was not added. SCHEDSTATS and TIMER_STATS remain enabled; they were not removed as an unmeasured optimization.

The full original feasibility assessment and its engineering estimates remain in [ASSESSMENT.md](C:/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research/ASSESSMENT.md). Its estimate ranges are judgments, not measured schedules or guarantees.

## 3. Newer-kernel port experiment: historical, stopped

A Qualcomm/Kyocera downstream 3.18 donor was identified in `saga0324/android_kernel_kyocera_afp`, branch `902/3/4KC`, pinned commit `652b4259bd6f6195beda2e55c0b36a090257bcd8`.

Downloaded reference configuration showed MSM8909, MDP3, WCNSS, fb1 extensions, 32-bit Binder and memory/seccomp support. The original KYF37 EVT/DVT device-tree include closure was checked: 28 files, including a shared skeleton outside the qcom directory. This established a donor lead, not device compatibility.

Scripts were prepared to compare sources, translate the effective configuration, copy the board include closure and attempt an isolated build. The large donor download did not complete: the WSL transfer ended with curl error 18. The download/continuation processes were stopped when the task shifted to improving the working kernel. No complete 3.18 kernel was compiled or booted.

Partial archives in this research folder and `/home/pablo/kyf37-kernel-port-research/donor.tar.gz` are historical inputs, not validated source packages. Do not resume the old continuation blindly. A future full port would first require a complete, pinned archive and a renewed board/driver/userspace compatibility audit.

Historical scripts: `compare-kernels.py`, `prepare-kyf37-318.py`, `build-318.sh`, `continue-318.sh`, `source-check.py`, `start-build.py`, `unpack-donor.py`. They are not the current performance build pipeline.

## 4. Implemented base backports

The first completed candidate is preserved in `backports-candidate/`. Its implementation is included in the latest performance candidate.

| Feature | Implementation and purpose |
|---|---|
| `/proc/meminfo` MemAvailable | Uses free pages, file LRUs, reclaimable slab and zone watermarks to estimate memory available to applications. ARM32 watermark subtraction explicitly casts operands to signed long to prevent unsigned underflow. |
| `getrandom()` | Real ARM EABI syscall 384; validates flags, bounds request length, waits for the existing entropy pool to initialize and returns EAGAIN for an uninitialized nonblocking request. Original entropy accounting is retained. |
| Newer zram frontend | Stable 3.18.140 code adapted to old bio iterators and allocator interfaces; LZO/LZ4 selection, multiple compression streams, discard/zero-page handling, limits and statistics. |
| LZ4 support | Compressor/decompressor sources and configuration backported from the same pinned stable tree. |
| Optional memory policy | LZ4, four streams, 256 MiB logical zram, 128 MiB allocator-page limit, page-cluster 0 and the existing swappiness policy of 100. Allocator/other metadata is additional to the page limit. |

Compatibility discoveries and fixes:

- ARM's legacy assembly syscall table requires a multiple-of-four entry count. Slots 382/383 remain unimplemented; getrandom occupies 384 and the table is padded to 388 entries.
- The older bio API iterates `struct bio_vec` pointers and uses `bi_sector`/`bi_size`; newer by-value iterator code was adapted accordingly.
- Existing allocator totals are reported in bytes. The zram frontend needs pages, so the compatibility wrapper shifts by PAGE_SHIFT.
- Compression working memory can fall back to vmalloc. Stream release must therefore happen after the allocator mapping/preemption state is released.
- Reducing the stream limit must detach idle streams under the spinlock and free them afterward. Freeing vmalloc-backed memory while holding the spinlock was avoided.
- The independent Git checkout initially caused an automatic `-g...-dirty` kernel release suffix. This was caught and removed through LOCALVERSION settings and a rebuild. The final release/vermagic is the original `3.10.49`; module checks were not bypassed.
- The tuned ramdisk removes competing legacy zram initialization and the old general-fstab zram entry, then uses a dedicated fstab and imported init file.

Pinned base references:

- [MemAvailable commit](https://github.com/torvalds/linux/commit/34e431b0ae398fc54ea69ff85ec700722c9da773).
- [getrandom commit](https://github.com/torvalds/linux/commit/c6e9d6f38894798696f23c8084ca7edbf16ee895).
- [Linux 3.18.140 reference](https://github.com/gregkh/linux/tree/6b1ae527b1fdee86e81da0cb26ced75731c6c0fa).

## 5. Added performance and battery work

### Allocator and compaction

Stable 4.1.52 zsmalloc was adapted into the isolated 3.10 kernel. It provides more flexible page packing, merged size classes and movable opaque handles needed for compaction. Original exported allocator function signatures and the 64-bit byte-count interface are retained. Internal allocation metadata changed and adds per-object handle storage; this has a memory cost.

The frontend exposes an explicit write-only zram `compact` control. The adapted handler accepts the value 1 and rejects invalid values or an uninitialized device. The balanced ramdisk requests one pass after `sys.boot_completed=1`. There is no recurring compaction daemon or maintenance timer.

**A meaningful failure was discovered in ARM emulation:** an imported compaction loop could repeatedly choose a source page containing only a pinned allocation without moving any objects. The harness timed out. A no-progress stop condition was added for that class pass, with the page returned to its list and lock state preserved. A later explicit pass can retry after the object is unpinned. The pinned-allocation regression case then passed.

Reference: [stable 4.1.52 zsmalloc](https://github.com/gregkh/linux/blob/c4ff7514e71ddb85d05f262cd40f841f494775c8/mm/zsmalloc.c), pinned commit `c4ff7514e71ddb85d05f262cd40f841f494775c8`.

### Power-efficient workqueues

Only the stable 3.18 power-efficient extension was transplanted; the existing workqueue core was retained. Explicitly marked work can use unbound execution rather than waking the issuing CPU. The default is enabled in this candidate and has the upstream-style kernel parameter.

Disk-event work was converted at the same sites as the stable reference. The framebuffer-console cursor conversion is included too, but CONFIG_FRAMEBUFFER_CONSOLE is disabled, so that conversion provides no active benefit in this build. Ordinary unmarked workqueues retain their existing behavior.

Reference: [stable 3.18.140 workqueues](https://github.com/gregkh/linux/blob/6b1ae527b1fdee86e81da0cb26ced75731c6c0fa/kernel/workqueue.c).

### CPU and storage policy

The original Qualcomm MSM8909 post-boot branch sets an 800 MHz CPU minimum and a two-core floor. Its interactive target-load string begins with 1 below 800 MHz, encouraging a rapid frequency increase even if the frequency floor is lowered.

The balanced policy addresses those settings together:

| Setting | New behavior |
|---|---|
| Kernel default governor | Interactive instead of performance, allowing scaling during early boot. |
| Post-boot governor | Select interactive only if listed as available. |
| Minimum CPU frequency | Use the positive `cpuinfo_min_freq` reported by the driver, only when it does not exceed the current maximum. No hardcoded new frequency/voltage table. |
| Interactive target loads | Set 85; retain existing hispeed frequency/load, timer and minimum-sample settings. |
| core_ctl minimum cores | Permit one at light load; retain automatic hotplug, existing thresholds and thermal controls. |
| Internal eMMC readahead | Reduce values above 128 KiB to 128 KiB; do not raise a smaller value or alter removable-storage queues. |

The existing Qualcomm setup still runs first. A ramdisk wrapper then runs the balanced policy and preserves the Qualcomm script's exit status. Missing controls and invalid readings are skipped. There is no polling loop. Vendor power services may subsequently override CPU settings; persistence is unverified.

The policy preserves the current maximum CPU frequency, voltage tables, thermal protection and charging controls. No overclock, undervolt, forced manual CPU offlining or I/O-scheduler replacement was added. Smaller readahead can hurt sequential workloads; lower floors can change latency. Their net benefit remains a hypothesis until measured.

Only three effective configuration options differ from the previous backport candidate: WQ_POWER_EFFICIENT_DEFAULT, CPU_FREQ_DEFAULT_GOV_PERFORMANCE and CPU_FREQ_DEFAULT_GOV_INTERACTIVE. The extracted-config audit checks that exact set.

## 6. Verification evidence and its limits

The latest [final-audit.json](C:/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research/performance-candidate/final-audit.json) records passing checks. Supporting reports reside beside it.

| Check | Result |
|---|---|
| Complete kernel and required modules | GCC 4.8 build completed, including independent Wi-Fi and core_ctl source builds. |
| Rebuilt vendor modules | All 15 checked; zero missing exports, symbol-CRC mismatches or unsupported loaded relocations. |
| Existing vendor modules | All 15 checked against the new kernel with the same zero-error results. Original release/vermagic retained. |
| Actual LZ4 code | 10,000 ARM32 Cortex-A7 emulation trials: varied pages, unaligned buffers, canaries and malformed/undersized buffers. |
| MemAvailable arithmetic | 10,006 ARM32 cases using the actual calculation with modeled counters. |
| getrandom | Static ABI wiring and linked-symbol checks; entropy readiness and real blocking behavior are not runtime-tested. |
| Compression-stream limit setter | Five ARM32 modeled list/lock/free cases; checked freeing outside locks and unmapping before stream release. |
| Actual adapted zsmalloc | 5,000 ARM32 allocations across small, medium, spanning, whole-page and random-size workloads; data retention, pinned objects, mapping modes, allocation failure, lock/mapping balance and complete page release. |
| One-shot CPU/storage policy | Six host-fixture scenarios; malformed/missing controls and unsupported governors handled, maximum preserved, repeated runs content-idempotent. Wrapper ordering and preservation of a simulated vendor failure exit status also checked. |
| Both boot images | Under 16 MiB; exact kernel, original OEM DT, boot geometry, legacy init, policy-version and boot-ID invariants verified. |
| Changed init scripts | Android 10 host_init_verifier passed. This does not prove runtime SELinux access to the added shell inputs. |
| Source integrity | Full patch matches the final independent source, applies to its baseline and is content-idempotent after both source scripts run. git diff --check passed. |
| Original files/artifacts | 47,017 original kernel files verified unchanged; previous candidate hashes checked unchanged. |

Synthetic compaction results, with one allocation pinned during the first pass:

| Workload | Pages before | Pages after | Objects moved |
|---|---:|---:|---:|
| 128-byte objects | 36 | 9 | 343 |
| 1024-byte objects | 268 | 72 | 379 |
| 2047-byte objects | 572 | 144 | 354 |
| 4096-byte objects | 250 | 250 | 0 |
| Random-size objects | 351 | 234 | 94 |

These deliberately fragmented, modeled pools are not estimates of phone RAM savings. The emulator harness uses one modeled CPU and simplified page/slab/locking primitives. It cannot validate real concurrency, OOM behavior, suspend, hardware drivers or energy use.

Existing vendor-tree Kconfig dependency warnings, the ARM return-address warning and duplicate DT recipe warnings remain. They were recorded, not represented as fixed. A temporary WSL connection timeout during a busy host period recovered without resetting the host or touching other build jobs.

No claims of fixed Wi-Fi, camera, modem disappearance, physical-panel tearing, Bluetooth, IMS/VoLTE or storage behavior were made. Boot success, calls, real zram pressure, thermal behavior and battery gains are unverified.

## 7. Result files and exact identities

| File in performance-candidate | Purpose |
|---|---|
| `boot-performance-balanced-unsigned.img` | Main result: new kernel plus memory/CPU/storage policies. |
| `boot-kernel-backports-unsigned.img` | New kernel with v13 release ramdisk preserved byte-for-byte; does not apply the balanced post-boot policy. |
| `zImage` | Compiled kernel. |
| `kernel.config` | Configuration extracted from that kernel. |
| `kernel-backports.patch` | Complete changes relative to the independent snapshot of the working baseline. |
| `modules/` | Fifteen rebuilt, audited modules. |
| `kyf37-performance-policy.sh`, `kyf37-performance-post-boot.sh` | Delivered one-shot policy and vendor wrapper. |
| `init.kyf37.memory.rc`, `fstab.kyf37.zram`, `ramdisk-init-review/` | Memory policy and reviewable init inputs. |
| `build-verification.json`, both module audits, `boot-packaging.json`, image validation JSONs, `final-audit.json` | Build and packaging evidence. |
| `zsmalloc-compaction-test.json`, `performance-policy-test.json`, `performance-implementation.json` | Additional test/implementation records. |
| Both provenance JSONs, `COPYING`, `LZ4-COPYRIGHT.txt` | Pinned reference identities, hashes and license material. |
| `SHA256SUMS` | Integrity manifest for the candidate contents. |

Exact hashes:

```text
Latest zImage, 6,894,352 bytes:
eaa4fc8b4d4aed71a0787a1c33a6649cd8a394fb01b48823718e424e4730e338

Balanced unsigned boot, 8,974,336 bytes:
220a24d25c6e04e9de2453b12d61f3cce55998a5567bd8eeb72cd1c1ff36b0a8

Kernel-only unsigned boot, 8,972,288 bytes:
66f6a8348783d6b7f43c9368c0576c95672bf6a61e69fa8a9588d00a2dbb0604

Original v13 unsigned boot used as packaging base:
b6a68e08c36b67a743f1444af96de5138d38e2547d88fd27f4eddade0033f4ad
```

The base image's relationship to the phone's currently installed image was not checked after the no-phone instruction. Both candidate images preserve OEM DT/geometry and exclude the development recovery-return timer/guard. They are unsigned boot artifacts, not an installed ROM or a new flashable installer ZIP.

## 8. Reproduction and script map

Current WSL source/build workspace: `/home/pablo/kyf37-kernel-port-research/backports`. Original folders remain references. This independent workspace now contains the performance changes; the older backports-candidate artifacts are frozen. Rebuilding the older stage requires a fresh baseline plus its saved patch, rather than assuming the current independent source is still the older stage.

| Scripts in kernel-port-research | Responsibility |
|---|---|
| `prepare-backport-workspace.py` | Snapshot working source and manifest; initialize independent Git baseline; copy effective config and external module sources. |
| `fetch-backport-references.py`, `fetch-performance-references.py` | Fetch pinned upstream inputs and write provenance/hashes. |
| `backport-working-kernel.py`, `backport-performance.py` | Apply guarded, re-runnable changes only to the independent kernel. |
| `build-performance.sh` | Apply both source stages, configure, build kernel/modules with GCC 4.8. |
| `test-arm-lz4.py`, `test-backport-interfaces.py`, `test-zram-backport-context.py` | Base component/ABI checks. |
| `test-zsmalloc-compaction.py`, `zsmalloc-test-shim.h` | Actual allocator ARM harness with modeled kernel primitives. |
| `test-performance-policy.py` | Host-only shell fixture and wrapper checks. |
| `verify-performance-build.py` | Config, linked symbols, modules, source preservation and final patch extraction. |
| `package-performance-candidates.py` | Reconstruct and validate two unsigned boot images from v13. |
| `final-performance-audit.py` | Repeatability, patch applicability, evidence consistency and candidate hash manifest. |

Execute in WSL Ubuntu, with the existing referenced compiler/Android host tools available:

```bash
root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research
python3 "$root/prepare-backport-workspace.py"
python3 "$root/fetch-backport-references.py"
python3 "$root/fetch-performance-references.py"
bash "$root/build-performance.sh" > "$root/logs/performance-build.log" 2>&1
python3 "$root/test-arm-lz4.py"
python3 "$root/test-backport-interfaces.py"
python3 "$root/test-zram-backport-context.py"
python3 "$root/test-zsmalloc-compaction.py"
python3 "$root/test-performance-policy.py"
python3 "$root/verify-performance-build.py"
python3 "$root/package-performance-candidates.py"
python3 "$root/final-performance-audit.py"
```

Stop if a command fails; do not proceed with a stale report. Tests use a qemu-user package unpacked locally under `backports/host-tools/qemu`, not a system-wide installation. Reproduction also depends on the working baseline, external source copies, GCC 4.8 and the existing Android host_init_verifier; the candidate directory alone is not a standalone source distribution/build environment.

Build logs: `logs/backports-build.log` for the older stage and `logs/performance-build.log` for the latest. No performance-kernel build remains running from this work. Other host jobs must not be interrupted.

## 9. Remaining ideas and future measurement design

These were discussed, not implemented:

- **Targeted stability audit/backports:** evaluate applicable upstream memory-management, locking and ext4 fixes individually. No blanket stable merge or comprehensive security audit has been performed.
- **PSI:** a possible later scheduler/reclaim backport for measuring CPU/memory/I/O pressure, followed by deliberate ROM low-memory-policy integration. Adding the interface alone does not guarantee faster behavior. [Kernel PSI documentation](https://docs.kernel.org/accounting/psi.html).
- **Optional task-delay accounting:** diagnostic build to distinguish CPU, storage and reclaim stalls; it has overhead and was not included as a performance feature.
- **Persistent crash-log integration:** pstore/ramoops support already exists; the board's reserved-memory configuration and capture/preservation would need review. No new RAM reservation was invented. [Ramoops documentation](https://docs.kernel.org/admin-guide/ramoops.html).
- **MDP3 tearing investigation:** targeted synchronization work could address the existing visible defect, but computer checks cannot establish its effect on the physical panel.

Further battery tuning requires measurement rather than assumptions. The proposed comparison plan is:

1. Compare a preserved baseline and candidate with comparable starting charge, brightness, radio state, network signal, ambient temperature and workload. Repeat comparisons and record duration/configuration.
2. Measure lid-closed idle for several hours: drain, suspend residency and sources of wakeups.
3. Repeat light keypad/app navigation: timings, CPU frequency residency, active cores and latency.
4. Compare calls and media: current draw, temperatures, audio stability and delays.
5. Exercise memory pressure: swap/compression activity, stalls, app reloads and peak memory.
6. Prefer validated current/energy measurements or an external meter where available. Short battery-percentage changes are too coarse to justify a gain claim. Driver current readings require checking units, sign and reliability.
7. Investigate the component responsible for drain before tuning it: CPU load, repeated wakeups, display, modem or other drivers can have different remedies. Keep thermal/charging protections and rollback intact.

**This is a future design only. No physical measurement scripts were prepared or run, and no baseline-versus-candidate battery experiment occurred.** Under the current restriction, further work can audit source, build, emulate components and prepare host-validated measurement tooling, but must not access the phone. Only a later explicit change to that restriction could permit hardware measurements.
