# KYF37 working-kernel backports

Built on 2026-10-08 from an independent snapshot of the working Android 10 Linux 3.10.49 kernel. Existing ROM/source/build folders remain unchanged. These are **unsigned, uninstalled experimental candidates**. No phone access occurred after the owner prohibited physical-phone testing.

## Implemented

| Feature | Purpose |
|---|---|
| `MemAvailable` | Estimate memory available to applications using file LRUs, reclaimable slab and zone watermarks; signed subtraction prevents ARM32 underflow |
| `getrandom()` | Standard ARM EABI syscall 384, with flag checks, bounded requests, initialized-pool waiting and nonblocking `EAGAIN`; original entropy accounting retained |
| Newer zram | Stable Linux 3.18.140 frontend adapted to the original allocator/bio APIs; LZO/LZ4 selection, multiple compression streams, discard/zero-page handling, memory limits and statistics |
| Optional memory boot policy | LZ4, four streams, 256 MiB logical swap, 128 MiB physical allocation limit, `page-cluster=0`, and the original swappiness policy of 100 |

These choices address the phone's limited RAM and useful Android/Linux interfaces while retaining its vendor drivers. LZ4 and multiple streams are intended to reduce compression overhead and serialization; speed, battery use and responsiveness have not been measured. Stream memory is released outside spinlocks and allocator mappings to accommodate vmalloc-backed working memory. The original zsmalloc ABI is retained, and no module checks are bypassed.

## Verification

- GCC 4.8 builds of the complete kernel and required modules, including separate Wi-Fi/core_ctl sources.
- Original `3.10.49` release/vermagic retained. Both the 15 rebuilt modules and 15 existing vendor modules pass exports, symbol-CRC and loader-relocation checks against the new kernel.
- Actual LZ4 sources pass 10,000 ARM32 Cortex-A7 emulation trials covering varied pages, unaligned buffers, output canaries and malformed/undersized input/output.
- Actual MemAvailable arithmetic passes 10,006 ARM32 cases. Static checks confirm syscall 384 and the padded 388-entry ARM table.
- Actual stream-limit setter passes five ARM32 tests with modeled lock/list/free primitives; source checks confirm unmapping before stream release.
- Both boot images fit the 16 MiB partition and pass exact-kernel, OEM-DT, boot-geometry, legacy-init/ramdisk and SELinux-policy checks.
- Android 10 `host_init_verifier` accepts the four changed/added init scripts. The zram fstab uses flags supported by the existing fs_mgr.
- The 47,017 original source files remain unchanged; independent `git diff --check` passes.

Existing vendor-tree Kconfig, ARM return-address and duplicate-DT-recipe warnings remain. These checks do not prove boot-time entropy behavior, kernel concurrency, swap under real pressure, hardware support or performance. Existing Wi-Fi, camera, modem and panel-tearing problems are not claimed fixed.

## Outputs

- `zImage`, `kernel.config`, `kernel-backports.patch`, `modules/`: compiled kernel, extracted configuration, complete new-source patch relative to the working snapshot and matching modules.
- `boot-kernel-backports-unsigned.img`: new kernel; v13 release ramdisk byte-for-byte unchanged.
- `boot-memory-tuned-unsigned.img`: same kernel with the optional memory policy; supersedes legacy zram initialization.
- `init.kyf37.memory.rc`, `fstab.kyf37.zram`, `ramdisk-init-review/`: reviewable policy and init inputs.
- `build-verification.json`, module audits, `boot-packaging.json`, image validation reports and `SHA256SUMS`: evidence and hashes.

Boot base: v13 release artifact, SHA256 `b6a68e08c36b67a743f1444af96de5138d38e2547d88fd27f4eddade0033f4ad`. Its relationship to the currently installed image was not inspected after the no-phone instruction. Neither candidate includes the recovery-return timer/guard. No signing key was accessed. Nothing was installed, signed or flashed.

## Reproduce

All Windows scripts/outputs are under `kernel-port-research`. WSL sources/tools/builds are in the new `/home/pablo/kyf37-kernel-port-research/backports` directory.

```bash
root=/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kernel-port-research
python3 "$root/prepare-backport-workspace.py"
python3 "$root/fetch-backport-references.py"
bash "$root/build-backports.sh" > "$root/logs/backports-build.log" 2>&1
python3 "$root/test-arm-lz4.py"
python3 "$root/test-backport-interfaces.py"
python3 "$root/test-zram-backport-context.py"
python3 "$root/verify-backport-build.py"
python3 "$root/package-backport-candidates.py"
python3 "$root/final-backport-audit.py"
```

Tests use a locally unpacked Ubuntu `qemu-user` package in `backports/host-tools`; download it there with `apt-get download qemu-user` when recreating the workspace. No system-wide installation is required. The source script is re-runnable and avoids rewriting identical content. The patch applies to the complete working snapshot, which already contains the older Android compatibility backports.

Primary references are pinned and hashed in `../backport-reference/provenance.json`: [MemAvailable](https://github.com/torvalds/linux/commit/34e431b0ae398fc54ea69ff85ec700722c9da773), [getrandom](https://github.com/torvalds/linux/commit/c6e9d6f38894798696f23c8084ca7edbf16ee895), [Linux 3.18.140](https://github.com/gregkh/linux/tree/6b1ae527b1fdee86e81da0cb26ced75731c6c0fa). The original source/build tree and rollback artifacts remain available. Owner signing and a separately authorized deployment are required before these candidates can be used.
