# Kernel hardening and display-sync candidate (builds on `performance-candidate`)

2026-10-08. Host-only. No phone access, signing or flashing. `performance-candidate-v1/` is the previous result, kept unchanged.

## Changes (all in `backport-hardening.py`, re-runnable; applied by `build-performance.sh`)

| Change | Why | Risk |
| --- | --- | --- |
| Binder: on thread free, `wake_up_poll(POLLHUP\|POLLFREE)` + `synchronize_rcu()` if the thread was ever polled (CVE-2019-2215 "bad binder" use-after-free; the backported binder lacked it) | local privilege escalation from any app that can use binder + epoll | Only threads that used `poll` pay the `synchronize_rcu` cost, which can sleep (called with the binder mutex held, a sleepable context). |
| MDP3 video mode: program `DMA_P_IBUF_ADDR` right after start-of-frame (blanking window) instead of at an arbitrary scan position; bounded 84 ms wait, falls through to the original path on timeout | possible cause of tearing seen only on the physical panel | Default **on**. Runtime off-switch: `echo 0 > /sys/module/mdss_mdp3/parameters/kyf37_vblank_sync`. Judging the visual result needs a person. |
| `CONFIG_DEBUG_GPIO` off | removes per-call debug code in the keypad GPIO path | none seen; no CRC change |
| eMMC: CFQ `slice_idle=0`, `group_idle=0` in the one-shot policy | CFQ idling helps spinning disks, not eMMC | skipped automatically if CFQ tunables are absent |

## A failure caught by the gate

Disabling `CONFIG_TIMER_STATS` changed symbol CRCs (`module_layout`, `hrtimer_*`, `kmalloc_caches`, ...): all 15 prebuilt Kyocera/Qualcomm modules failed `existing-module-audit`. It was reverted (`--enable TIMER_STATS` in `build-performance.sh`). Lesson: any struct-layout-affecting config option (timer/sched/debug accounting) breaks the proprietary modules; only options with no CRC effect are safe. The first packaging attempt after the failed audit used a stale kernel because the commands were chained through a pipe; the final run used strict `&&` and reran verify, package and final audit.

## Results

* `verify-performance-build`, `package-performance-candidates`, `final-performance-audit`: pass. 15/15 rebuilt and 15/15 existing modules: zero missing exports, CRC mismatches or unsupported relocations. Original `3.10.49` release/vermagic retained.
* New `zImage` SHA-256 `125f9f53…542c`; balanced boot `94eb329d…a38` (8,974,336 B); kernel-only boot `18bc2484…2fe1` (8,972,288 B). Both unsigned, under 16 MiB.
* Parameters present in `vmlinux`: `mdss_mdp3.kyf37_vblank_sync`, `kyf37_porch_us`.

## Not verified

Everything on hardware: boot, tearing, binder behaviour under load, battery, I/O. Install order when testing is allowed: kernel-only boot first (`boot-kernel-backports`), then the balanced policy; keep the stock rollback.
