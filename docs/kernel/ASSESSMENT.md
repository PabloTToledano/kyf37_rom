# KYF37 newer-kernel feasibility assessment

Date: 2026-10-08. Scope: retain the existing Android 10 ROM and original partition layout while replacing its Linux 3.10.49 kernel. All new work for this assessment lives in this folder. Existing Windows files and WSL source/build trees were read only. No build, signing, device write, reboot, or flash was performed.

## Verdict

Possible in principle, but this is a hardware enablement and vendor-interface port, not a kernel replacement by configuration alone. A Qualcomm downstream 3.18 tree is the most plausible first experiment. It is still a substantial project with uncertain results. A maintained 6.x kernel is a much larger undertaking that could require replacing parts of the ROM's graphics, camera, audio, and modem integration.

If the purpose is to fix tearing, Wi-Fi, camera, or a scheduler crash, targeted fixes on the working 3.10 branch are likely cheaper and easier to validate. A newer version alone does not demonstrate a fix for any of these problems. If the purpose is long-term security maintenance, 3.18 is an intermediate technical experiment rather than a maintained destination.

Planning estimates below are engineering judgments for one experienced developer with access to this phone, not measured schedules or promises. A successful build is much easier than a dependable daily-use ROM.

| Route | Difficulty | Rough effort and practical outcome |
|---|---|---|
| Selected backports on current 3.10.49 | Moderate, depending on subsystem | Days to weeks for a narrow change; preserves most working hardware integration |
| Move toward final upstream 3.10 stable patches | High | Weeks to months of conflict resolution and regression checks; Qualcomm changes complicate wholesale merges, and the branch is obsolete |
| Qualcomm/Kyocera 3.18 | Very high | Several weeks to a few months for an initial boot/ADB milestone; roughly 3–6+ months for substantial hardware parity, with blockers possible |
| Qualcomm 4.4/4.9 | Very high to extreme | Many months; donor coverage of this exact SoC and legacy interfaces must be demonstrated first |
| Maintained 6.x | Extreme | Potentially 6–12+ months, or longer, for useful integration; full hardware parity cannot be promised |

## What the existing project establishes

- The inspected WSL kernel is 3.10.49, with origin `saga0324/android_kernel_kyocera_afp` and HEAD `57a11bec679273e797cbf3fcb3fc1488637b3fe6`. It has substantial uncommitted Android compatibility changes: `git diff --stat` reports 41 tracked files, 2,555 insertions and 527 deletions. A clone at HEAD alone would lose these changes; the count also does not inventory untracked files.
- The current tree includes Binder, SELinux, memory-management and scheduler changes. The handoff records Binder/hwbinder/vndbinder, policy version 30, MEMCG and seccomp support. A donor must satisfy the actual built ROM requirements rather than merely use a newer version number.
- The project records a hardware-booted GCC 4.8 kernel and failures with a GCC 4.9 build. The exact failure mechanism was not proved. GCC 4.8 is a constraint of the existing source/build path, not a rule that every newer donor must use it.
- `KYF37_defconfig` enables MDP3, KGSL, Qualcomm ION, WCNSS/Pronto, SMD, RPM regulators, MSM SDHCI, camera sensor support, Kyocera sound features, motion-sensor features and Kyocera security/logging extensions.
- The module audit records matching 3.10.49 modules with versioned symbols. The handoff documents rebuilding Wi-Fi and core_ctl after stock module CRC mismatches. Existing `.ko` binaries must not simply be carried into a newer kernel or force-loaded.
- The local BoardConfig selects 32-bit ARM, Adreno 304, legacy ION, HWC1, 32-bit Binder, legacy boot header 0 and an OEM DT image. Boot capacity is 16 MiB. The packaging script preserves legacy ramdisk/rootfs behavior and configures ADB through `/sys/class/android_usb/android0`.
- `KYF37-SECONDARY-SCREEN.md` identifies the OEM `disp_ext_sub*.c` driver family, `/dev/graphics/fb1`, and a 128x36 visible panel with 128x72 framebuffer allocation. That interface is part of the ROM's working feature set.

## Hardest dependencies

| Area | Why it matters | Port acceptance criterion |
|---|---|---|
| Boot and board description | OEM bootloader selection, memory map, interrupts, clocks, regulator and pinctrl bindings can differ | Signed image fits the original boot partition and boots with a correctly rebuilt board DT; no assumption that the old DT fits the donor |
| eMMC, USB and power | Without storage and ADB, faults become difficult to diagnose; broken suspend or charging can undermine daily use | Readable partitions, reliable ADB, charging and repeated sleep/wake without filesystem errors |
| Main display, GPU and buffers | MDP3/KGSL/ION ioctls and private buffer layouts are coupled to existing HALs and blobs | Main panel and accelerated composition work with correct synchronization; physical tearing requires owner observation |
| Modem and audio | Existing firmware/RIL expect SMD, QMI/RMNET and Qualcomm audio interfaces; booting Android does not prove calling | Modem channels remain available; calls, bidirectional audio, data and suspend recovery pass |
| Wi-Fi and Bluetooth | WCNSS firmware handshakes, board data and driver generation must agree | Real firmware initialization and connectivity; no fabricated download flags or calibration data |
| Camera | Legacy HAL uses private camera ioctls and sensor/power integration | Compatible control paths and a real preview/capture; existing AEC failure is not presumed solved |
| Flip-phone features | Keypad, lid, side key, fb1, LEDs, vibration and infrared depend on OEM drivers and nodes | Existing application-visible behavior survives or is deliberately adapted inside the experiment |
| Android interfaces | Binder width, SELinux, cgroups, seccomp, allocator/fence behavior and init USB paths must match userspace | Full boot and service operation, not just a kernel log or boot animation |

Linux does not promise a stable internal driver ABI across kernel releases. Source adaptations and rebuilding modules are expected: [Linux driver-interface documentation](https://docs.kernel.org/process/stable-api-nonsense.html).

## Best donor lead, and its limits

The repository supplying the current source lists Kyocera 902KC/903KC/904KC sources at Linux 3.18.71, CAF `LA.UM.6.7.r1-08500-8x09.0`, with `90234KC_defconfig`. This is a useful lead because it could preserve more Kyocera conventions than a generic kernel. The same table lists KYF37 at 3.10.49.

Source: [Kyocera kernel-source collection](https://github.com/saga0324/android_kernel_kyocera_afp).

This assessment verified the listing, not a compatible donor. The 3.18 branch contents, exact SoC configuration, MDP3 availability, panel and PMIC compatibility, and proprietary-interface differences still need an isolated source comparison. Shared manufacturer and a CAF `8x09` label are insufficient evidence of interchangeability. No working KYF37 newer-kernel port was established by this research.

For a maintained destination, consult [kernel.org's active releases](https://www.kernel.org/releases.html). The older 3.10, 3.18, 4.4 and 4.9 lines are outside that active long-term list. A vendor tree's larger version number does not itself establish security coverage.

## Recommended isolated experiment

1. Keep future scripts, donor source, outputs and logs under `kernel-port-research/`, or a separately created WSL experiment directory. Do not run the existing staging scripts: they write into the current ROM tree. Do not change existing worktree registrations.
2. Inventory the effective current kernel config, tracked changes, untracked source additions and external module sources. Record hashes of public inputs without accessing or copying the owner private key. Preserve the existing source/build trees as references.
3. Fetch and pin only the candidate 3.18 donor in the new experiment. Compare SoC support, DT bindings, MDP3/KGSL/ION UAPI, SMD/audio, WCNSS and Kyocera extensions. Reject it early if core MSM8909 support is absent or the ROM's binary interfaces require disproportionate replacement work.
4. Use re-runnable Python port scripts with explicit source/output paths restricted to the experiment. First target a minimal board build with storage, serial logging and USB ADB. Compile all required modules against that build. Keep the existing Android system as the first compatibility target.
5. Before hardware testing, verify original geometry, partition size and signing workflow, and preserve a verified previous boot image and stock rollback. The current image validator expects the existing kernel/DT; an experimental validator must check the new artifacts independently without weakening the production gates.
6. A later hardware trial should change only the permitted boot image initially. Leave recovery, keystore, modem/persist/NV and userdata untouched. Do not ship the old diagnostic recovery timer or misc guard. Kernel-induced filesystem damage remains a real testing risk, even without an intentional data wipe.
7. Progress through boot/ADB, display/keypad, storage and charging, modem/audio, sleep/wake, then remaining peripherals. Verify boot completion, service crashes and at least 15 minutes of initial stability; follow with repeated cold boots, calls, lid cycles and longer idle tests. Only claim features actually tested.

The next useful investment is a bounded donor comparison, not a flash. It should answer whether a 3.18 tree retains the hardware and ABI pieces above. If it does, an experimental port is defensible; otherwise, improving the existing kernel is the stronger route for this ROM.
