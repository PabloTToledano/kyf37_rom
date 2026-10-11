# KYF37 PCM config ABI fix — 2026-10-09

The owner's audible-silence report was correct. The Bad Apple media player and AudioFlinger showed started tracks and nonzero samples, but the proprietary HAL repeatedly failed ALSA SW_PARAMS with EINVAL and closed the PCM stream. The earlier full-video test established video completion/player state, **not audible music**.

The installed Kyocera HAL exports 36-byte `pcm_config_deep_buffer` and `pcm_config_low_latency` objects. Their final offset-32 field is `avail_min` (240 / 60). Android 10 tinyalsa has a 40-byte `pcm_config`: offset 32 is `silence_size`, offset 36 is `avail_min`. Thus it read the old 240 as silence_size with silence_threshold=0; Linux 3.10 rejects this in `snd_pcm_sw_params`. It also read beyond the stock structure for avail_min.

`device-inspection/fix-android10-audio-pcm-config-abi.py` adapts pcm_open only when dladdr identifies `audio.primary.msm8909.so`: copies the 32 common bytes, moves the old final word into avail_min, leaves silence_size zero, and writes refined period sizes/counts back safely. Modern callers keep their original ABI. libdl is an Android-only build dependency; host variants remain buildable. The first build failed because libdl was initially added to the host variant; this was corrected, and `~/audio-pcm-abi-build2.log` passed.

Evidence: `stock-pcm-config-audit.json` extracts the actual installed HAL objects; `verify-config-abi.py` uses the real patched source against a guard-page 36-byte allocation and checks an unchanged modern caller. Both pass. Actual library installed atomically at `/system/lib/libtinyalsa.so`, audio HAL/audioserver restarted, then a clean sync/reboot completed. Reboot resolves the old mapped/unlinked library preventing RO remount. The fixed SHA-256 persisted and `/system` is now RO.

Before SHA-256: af33efda2861662097645bd8ca6174dd0f145165bccad7beca59b77671856f7b
Fixed SHA-256: 6bfeb66325b62692a513bbd178cad95f4bfd01b55c4fbd076a17011b8dc44b32
Rollback library: `libtinyalsa-before.so`; fixed artifact: `libtinyalsa-fixed.so`. Restore using the same temporary-WP-clear / atomic system-library replacement / sync / clean reboot process. No boot, recovery, userdata or modem partitions were flashed.

Hardware after fix: Bad Apple media player active; speaker PCM0 state RUNNING, hardware and application pointers advancing, SPK DAC Switch On, unmuted speaker media output. Short/hold/video/audio-start/single-stop/audio-release/lid/main-screen checks all pass after reboot (`../outer-animation/badapple-hardware-verification.json`, `badapple-pcm-running.txt`, `badapple-speaker-mixer.txt`). An initial immediate post-reboot event test was inconsistent; a later complete rerun passed without further changes. No microphone recording or claim of direct listening was made.

Reproduce: run the fix script in WSL, build `libtinyalsa` through `build-locked.sh`, stage its system/lib output. On phone hold the lock; save the old library; run clear-system-temp-wp; remount system RW; stage the new library in `/system/lib`, chmod/chown/chcon, rename atomically; sync; restart vendor.audio-hal-2-0 and audioserver; sync/reboot; verify hash and RO mount. Next fresh ROM builds include this source fix; existing installer ZIPs remain unchanged.
