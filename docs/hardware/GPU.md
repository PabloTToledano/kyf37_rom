# GPU.md — Adreno 304 / MDP3 display path / tearing investigation (gpu agent, revisions v30–v39)

Owner of this doc: the **gpu** agent. Newest entries are appended at the bottom of the log; the summary table comes first.
Everything here is labelled **MEASURED** (observed on the phone), **ANALYSIS** (proved by reading code), or **BUILT-ONLY / OWNER-EYES**
(needs a human looking at the panel).

## 0. Hazards found (read before touching the display from a shell)

* **NEVER `cat /sys/kernel/debug/mdp/panel_reg` (or write `panel_off`/`panel_reg`) on this MDP3 kernel.** Those debugfs
  files are MDP5 code that dereferences `mdss_res->ctl_off[0]` (does not exist on MDP3): **kernel panic + reboot**
  (2026-10-08 18:07, `/proc/last_kmsg`: "Kernel panic - not syncing: Fatal exception"). Panel DCS registers cannot be read this way.
* Do not write a bad `MDP3_REG_DMA_P_IBUF_ADDR` through `/sys/kernel/debug/mdp/reg` and leave it there: the MDP IOMMU faults on
  every frame (hundreds of `msm_iommu_v1: Unexpected IOMMU page fault!` lines). Writing the register back (or any new SF frame) cures it.
* `/sys/kernel/debug/mdp/reg` + `off` (`echo '<hexoff> <hexcount>' > off; cat reg`) is a safe read-only MDP register window
  (MDP base 0x1A00000; DMA_P at 0x90000, DSI video timing at 0xF0000).

## 1. Facts about the display path (MEASURED unless noted)

| Item | Value |
|---|---|
| Panel | `kc jdi fwvga video mode dsi panel`, DSI video, non-burst sync-event, 2 lanes, 480x854, 24 bpp |
| Timing (regs 0xF0000..) | 548 clk/line x 864 lines = 473,472 clk/frame, pclk ~28.4 MHz, 60.0 Hz; **vblank only 10 lines (~193 us)**: vfp 6 / vsync 1 / vbp 3 |
| MDP | MDP3 v3.05 (`hw_rev=305`), single DMA_P pipe, no overlay pipes; SELinux permissive |
| DMA_P regs | CONFIG 0x0418123f, SIZE 480x854, STRIDE 0x780 (=1920=480*4), FETCH_CFG written 0x40 |
| Scanout buffers | HWC1 posts the SF client target through `MSMFB_OVERLAY_PLAY`; IOVAs alternate **0x200000 / 0x400000** (2 buffers in v13: `NUM_FRAMEBUFFER_SURFACE_BUFFERS=2`) |
| Underruns | `/sys/kernel/debug/mdp/stat`: `underrun: 0` after sustained UI use; no `display underrun` in dmesg |
| SF/HWC | Hwc2On1Adapter over `hwcomposer.msm8909` (CAF msm8916 HWC1, MDPVersion=305); everything CLIENT composited into one FB target; `PresentFenceIsNotReliable` |

## 2. Experiment log

### 2026-10-08 — E1: is the MDP3 buffer-address register latched at start-of-frame? (answers the lead's top hypothesis)

Question: `mdp3_dmap_update()` writes `DMA_P_IBUF_ADDR` immediately and only then waits for SOF. Commits arrive at arbitrary phase
(trace: write -> next SOF was 0.02 ms, 3.1 ms, 6.5 ms ... i.e. up to 40 % of a frame before SOF). If the register were live
the lower part of the screen would come from the new buffer = a tear line at a random height.

Method (MEASURED): kprobes on `mdp3_dmap_update` (arg buf), `mdp3_vsync_intr_handler` (SOF) in ftrace; then via debugfs
`mdp/reg` write an **unmapped** IOVA (0x3f000000) into `DMA_P_IBUF_ADDR` for a short window and watch the MDP IOMMU fault log.
* Window of ~90 us in the middle of a frame, repeated 12 times (script `device-inspection/gpu-ibuf-latch-test.sh`): **0 IOMMU faults**.
  A live register would fault within one line time (19 us) because the DMA fetches continuously.
* Window of 7+ ms: fault appeared **7.2 ms after the write** (= next frame start), not immediately.

**Verdict: the register is shadowed and taken at frame start.** Writing it mid-frame is safe; the address-write timing in
`mdp3_dmap_update` is NOT the cause of tearing. (The kernel's own `vsync_status` logic also assumes "taken at the next SOF".)
Writing the address inside the SOF IRQ would only matter for latency, not for tearing. **No kernel change needed for this.**

### 2026-10-08 — E2: fence/buffer-lifetime audit of the whole chain (MEASURED + ANALYSIS)

ftrace of one UI run (Settings navigation) with `kgsl:*`, `sync:*`, kprobes, atrace:
1. SF GPU composition (5 IBs, ~1.5 ms submit, ~5 ms to retire) -> native fence `kgsl-3d0-pid-..-ts-N`.
2. HWC thread: `MSMFB_BUFFER_SYNC` (kernel `mdss_fb_sync_get_fence` val=N twice: release + retire) then the `mdss_fb0` commit thread
   does `sync_wait kgsl-... state=1` (**GPU fence already signalled every time: the buffer is complete before the address is written**).
3. `mdp3_dmap_update` writes the address, waits SOF (`mdp3_wait_for_vsync_comp`), then `mdss_fb_0` timeline +1 (release/retire fences).
4. Right after, SF's *next* GPU job shows `kgsl:syncpoint_fence ctx=1 fence=mdp-retire`: the GPU waits on the retire fence of the frame just
   posted, which expires at the SOF that latches it. FramebufferSurface uses that as the release fence of the previous buffer ->
   **a buffer is only reused after the SOF that replaced it**. Correct for double buffering.
So there is no software path in which the GPU overwrites a buffer that is being scanned out, and the scanned buffer is always complete.
(Kernel: video panel `threshold=2`, retire_threshold=0 -> release fence N and retire fence N signal when frame N is latched, as measured.)

### 2026-10-08 — E3: underflow / bandwidth (MEASURED)
`/sys/kernel/debug/mdp/stat` `underrun: 0` before and after a Settings scroll run with two `dd` memory hogs running (also 0 after long
normal use). No `display underrun detected` in dmesg. DDR bandwidth/MDP FIFO underflow is therefore NOT the cause. The MDP clock
is SVS rate and bus vote is honest (480*864*4*60 = 99.5 MB/s).

### 2026-10-08 — E4: cadence (MEASURED)
Trace of 210 commits in a Settings navigation (`device-inspection/gpu/trace-ui-settings-v13.txt`, analysed by `analyze-commits.py`):
159 commits 1 frame apart, 33 two frames apart, the rest idle gaps. Buffers alternate 0x200000/0x400000 exactly (105/105): nothing
else (no FBIOPAN, no foreign client) posts to fb0 while SF runs. GPU composite takes ~5 ms; the fence is always signalled before commit.
"GPU missed frame count" in `dumpsys SurfaceFlinger` is an artifact of `PresentFenceIsNotReliable`.

### 2026-10-08 — conclusions after E1-E4
Everything between "GPU fence signalled" and "address latched" is provably consistent: complete frames, never overwritten while scanned,
no underflow. The remaining candidates, none provable without looking at the panel:
1. **Memory type difference vs stock.** Stock Android 5.1 scanned the kernel-owned, uncached, contiguous fb0 pages (`MDP_MEMORY_ID_TYPE_FB`).
   Android 10 scans **cached ION system-heap pages mapped with IOMMU_CACHE** (gralloc default: cached unless SW_*_RARELY; the SF client
   target usage 0x1a00 has none). `mdp3_get_img` does no cache maintenance. Switch S1 below.
2. DSI link / panel-side errors (cannot be read: MDP3 has no working panel-register debugfs, see hazard above; needs a kernel patch).
3. Frame cadence/judder perceived as tearing (no tear mechanism found in software).

### Switches / tools shipped for owner testing
| id | What | How to flip |
|---|---|---|
| S1 | HW_FB (client target) ION buffers uncached | `fix-android10-gpu-fb-uncached.py` patches gralloc.msm8909. `setprop persist.kyf37.fb_uncached 0\|1` (default 1) then restart SurfaceFlinger (buffers are allocated at SF start) |
| T1 | `device-inspection/gpu/fbtear` | Direct fb0 page-flip test (white bar bouncing, SurfaceFlinger stopped). Tear-free here but torn under Android => cause is in SF/GPU/HWC/ION; torn here too => panel/DSI/kernel. `adb push fbtear /data/local/tmp/; adb shell "stop; chmod 755 /data/local/tmp/fbtear; /data/local/tmp/fbtear; start"` (~30 s) |
| M1 | zram swap: v13 had **no swap at all** (`/proc/swaps` empty; the `ro.config.zram` trigger never fires for a build.prop value) | `fix-android10-gpu-memory-perf.py` -> `init.kyf37.gpu.rc` (384 MB zram, swappiness 80, at boot_completed). Verified live: disksize/mkswap/swapon work |

### Research notes (GPU blob)
Web search found no msm8909 proprietary-files listing for newer Adreno 304 userspace. Reasoning: Android 8.1 era Adreno blobs (Nokia 2,
Android Go) need `IOCTL_KGSL_GPU_COMMAND` (kernel 3.18); this 3.10.49 kgsl lacks it, so they are not ABI compatible. Only a 6.0-era blob
(LG K7/K8 msm8909, kernel 3.10) would be compatible, with marginal gain over AU@05.01; not pursued.

### 2026-10-08 evening — build status
`~/gpu-build.log`: incremental build with S1 (gralloc uncached) and M1 (init.kyf37.gpu.rc) **completed successfully** (BUILD_EXIT=0, 3m16s).
NOT yet flashed or tested on hardware: the phone lock was held by the radio agent until 21:14. Next steps when the lock is free:
bind-mount the new gralloc.msm8909.so, restart SF, run `fbtear`, verify zram after reboot, then package v30.

(continued below as the investigation proceeds)

### 2026-10-09 — Is GPU 2D/3D acceleration working? Yes (MEASURED, Claude, lead session)
Request was to "fix GPU 2D and 3D acceleration"; measuring first showed nothing is broken in the acceleration path itself:
* `dumpsys SurfaceFlinger`: `GLES: Qualcomm, Adreno (TM) 304, OpenGL ES 3.0 V@100.0 AU@05.01.00.036.053`; SF composites with GLES (`RenderEngine`), all HWC layers CLIENT.
  All-CLIENT is inherent: MDP3 on msm8909 has a single DMA_P pipe and no overlay pipes, so there is no hardware 2D composition to enable.
* Apps: `dumpsys gfxinfo` → `Pipeline=Skia (OpenGL)` (HWUI 2D drawing is on the GPU). Settings scroll test (30 down + 30 up D-pad presses, 156 frames):
  p50 13 ms, p90 29 ms, p95 40 ms, 33 % janky (first-frame shader compiles dominate p99).
* Offscreen GLES2 benchmark `device-inspection/gpu/gles_bench.cpp` (module `kyf37_gles_bench`, built by `fix-android10-gpu-bench.py`; prebuilt binary `device-inspection/gpu/kyf37_gles_bench`,
  `adb push` and run, no root needed) on the real kgsl driver, GPU at 307 MHz (max 409.6 MHz, governor `msm-adreno-tz`):
  flat fill 1.22 ms/frame (335 Mpix/s), textured blend (2D-style blit) 1.31 ms (313 Mpix/s), ALU-heavy 24x sin/cos shader 48.8 ms (8.4 Mpix/s, expected for a 304),
  256x256 texture upload 0.49 ms (532 MB/s), `GL_ERROR 0`.
* `kgsl-3d0/reset_count` rises ~2/s even when idle, with no kgsl/hang lines in dmesg: it counts power-collapse restarts, not hangs.
So the remaining visible UI problems (jank, tearing) are not "GPU acceleration missing": fill rate is ~800 fps; look at CPU side (cores 1-2 offline via core_ctl, JIT off, 1.09 GHz A7) and the display path (tearing, owner-eyes only).

### 2026-10-11 — UI smoothness tuning (MEASURED, claude-gpu, lead session)
Benchmark: `tools/gpu-jank-test.sh <label>` (Settings, 30x D-pad down + 30x up, `dumpsys gfxinfo` jank), matrix in `tools/gpu-matrix.sh`. Two runs per cell; run-to-run noise about ±4 points.

| core_ctl min_cpus | GPU devfreq min_freq / idle_timer | janky frames | p95 |
|---|---|---|---|
| 2 (stock config) | 200 MHz / 50 ms (default) | 42-58 % | 32-61 ms |
| 2 | 409 MHz / 1000 ms | ~30 % | 27 ms |
| 4 | 200 MHz / 50 ms | 26-31 % | 24-93 ms |
| 4 | 307 MHz / 200 ms | 19-20 % | 23 ms |
| 4 | 307 MHz / 1000 ms | 19-22 % | 22 ms |
| 4 | 409 MHz / 50 ms | 14-19 % | 20-22 ms |
| 4 | 200 MHz / 1000 ms | 37-41 % | 30 ms |

Findings: (1) core_ctl kept cores 2-3 offline (`min_cpus=2`); keeping all four online roughly halves jank; (2) the GPU dropping to 200 MHz between frames costs another ~10 points; `idle_timer` has no effect; (3) CPU `scaling_min_freq` pinned at 1094 MHz adds little over the existing 800 MHz floor. Chosen: `min_cpus=4` and GPU `min_freq=307.2 MHz` (about the same smoothness as 409 MHz, less power) via `init.kyf37.uiperf.rc` (`fix-android10-gpu-ui-perf.py`, chained in the build wrapper). Applied live on the phone with the same values (jank 20 %, p50 13 ms, p95 21 ms); the init file takes effect with the next ROM build. Power cost was not measured; if battery life suffers, set `min_cpus` back to 2 first. Tearing on the physical panel is unchanged and still needs owner eyes.
