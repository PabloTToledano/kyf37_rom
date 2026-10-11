# KYF37 performance and battery candidate

This is an **unsigned, uninstalled experimental candidate**, built from the working Android 10 Linux 3.10.49 kernel in the separate `kernel-port-research` workspace. The original ROM/kernel/source directories and previous candidate artifacts are preserved. No phone access, signing, flashing or hardware testing is part of this work. Performance and battery gains have not been measured.

## Added changes

| Change | Purpose and tradeoff |
|---|---|
| Stable 4.1.52 zsmalloc | More flexible page packing, merged size classes and movable opaque handles; adds per-object handle metadata |
| Explicit zram compaction | Consolidates fragmented allocations to release pages; skips pinned objects and stops a class pass when no progress is possible |
| One compaction pass after Android boot completes | Reclaims startup fragmentation without a recurring timer; can briefly consume CPU during that pass |
| Stable 3.18 power-efficient workqueues | Allows disk-event work to run without binding it to the issuing CPU; framebuffer-console cursor conversion is included but that console is disabled in this configuration |
| Interactive default CPU governor | Replaces the maximum-frequency performance governor during early boot; retains demand-based frequency scaling |
| Balanced post-boot policy | Runs once after the existing Qualcomm setup; lowers the 800 MHz floor to the minimum reported by the CPU driver, changes interactive target load from the low-frequency value of 1 to 85, and permits core_ctl to retain one core at light load |
| Bounded eMMC readahead | Reduces values above 128 KiB to 128 KiB to limit speculative reads and RAM use; sequential workloads may benefit from larger readahead |

The candidate retains the previous MemAvailable, getrandom, LZ4/multistream zram and bounded swap policy: 256 MiB logical swap, a 128 MiB allocator-page limit (metadata is additional), four compression streams, page-cluster 0 and swappiness 100.

The CPU policy preserves the maximum frequency, interactive hispeed/timer settings, automatic core control, voltage tables and thermal protections. It makes no modem, Wi-Fi, camera, GPU, panel, charging or filesystem-format changes. Vendor power services may subsequently adjust CPU values; persistence has not been verified. Missing controls and invalid frequency readings are skipped.

Additional accounting, recurring maintenance, speculative scheduler/voltage changes and blanket stable-kernel merges were excluded because they lack demonstrated benefit for this device or add overhead/risk. Persistent crash logging already has kernel support; no new reserved-RAM address was invented.

## Validation and limits

The allocator test runs the actual adapted C implementation under ARM32 Cortex-A7 emulation with modeled page/slab/lock primitives. It covers 5,000 allocations, multiple size distributions, fragmentation, pinned objects, read/write mapping, allocation failure and release of all pages. It exposed a no-progress compaction loop in the imported implementation; the added stop condition fixes that test. This is not a concurrent kernel or hardware test.

In the synthetic fragmented pools, the first compaction pass reduced pages from 36 to 9, 268 to 72, 572 to 144 and 351 to 234. Whole-page allocations remained at 250 pages. These are artificial test results, not estimates of memory savings on the phone.

The one-shot shell policy passes six host-fixture cases, including absent controls, unsupported governors, bad/zero minimum readings and a minimum above the current maximum. It preserves the maximum and is content-idempotent. Host fixtures do not prove sysfs permissions or SELinux behavior.

Final build, module, boot-image and source-preservation evidence is recorded in the accompanying JSON reports and `SHA256SUMS`. The complete candidate must pass those checks before delivery. Existing vendor-tree Kconfig and ARM/DT warnings remain. Boot, suspend/resume, calls, real memory pressure, concurrency, display quality and battery consumption remain unverified.

## Artifacts

- `boot-performance-balanced-unsigned.img`: new kernel plus memory and balanced post-boot policies.
- `boot-kernel-backports-unsigned.img`: new kernel with the original v13 release ramdisk byte-for-byte preserved. It includes kernel power/allocator changes but does not apply the balanced post-boot policy.
- `zImage`, `kernel.config`, `kernel-backports.patch`, `modules/`: compiled kernel, effective configuration, full patch against the working baseline and matching modules.
- `kyf37-performance-policy.sh`, `kyf37-performance-post-boot.sh`, `init.kyf37.memory.rc`: delivered policy inputs.

Both boot images retain OEM device trees and boot geometry. Neither has the development recovery-return timer. Nothing has been signed or installed. The owner's signing key was not accessed.

## Reproduce on the computer

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

All source modifications use re-runnable scripts confined to `/home/pablo/kyf37-kernel-port-research/backports/kernel`. The previous `backports-candidate` outputs are frozen; the independent source workspace now includes this additional performance work. The patch also permits reconstruction in a fresh copy of the baseline.

References are pinned and hashed in `performance-provenance.json` and `base-provenance.json`: [stable 4.1.52 allocator](https://github.com/gregkh/linux/blob/c4ff7514e71ddb85d05f262cd40f841f494775c8/mm/zsmalloc.c), [stable 3.18.140 workqueues](https://github.com/gregkh/linux/blob/6b1ae527b1fdee86e81da0cb26ced75731c6c0fa/kernel/workqueue.c), [CPU frequency scaling](https://docs.kernel.org/admin-guide/pm/cpufreq.html), [zsmalloc documentation](https://docs.kernel.org/mm/zsmalloc.html).
