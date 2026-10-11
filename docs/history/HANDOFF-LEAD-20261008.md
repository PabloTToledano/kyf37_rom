# Lead handoff — state at 2026-10-08 ~20:15 (read AGENTS.md first, then this file)

Written so another LLM can continue without the chat. Everything below is either **verified** (observed on the phone / in build output) or marked
**unverified**. Sub-documents: `AGENTS.md` (project map, pipeline, gotchas), `AGENT-BRIEFING.md` (multi-agent rules), `KEYPAD.md`, `MICROG.md`, `TV.md`,
`RADIO.md`, `GPU.md`, `KYF37-USB-RECOVERY-RUNBOOK.md` (dead-phone recovery), `modem-investigation/tv-tuner/README.md`.

## 1. Where the phone is right now
* Phone `981108631314` is running Android 10, **an older image than v15**: v13 plus live patches (Cipo camera libs, Wi-Fi rc, keypad privapp xml). **microG, Aurora Store, the Phone-settings app,
  OEM ringtones, wallpaper, the latest boot animation, radio/Wi-Fi fixes are NOT on the phone yet** (checked: `pm list packages` has no gms/vending/aurora).
* Phone lock (`tools/phone-lock.ps1 status`) was FREE at the last check. No agent holds the phone. The owner cancelled my queued v15 flash; **v15 was never installed**.
* The SD card has `/external_sd/kyf37-android10-go-20261007-twrp-v12.zip`, `…v13.zip`, and 9→(see below) rollback folders; the **stock** backup is rollback folder `KYF37-Android10-rollback-19691231-191652-367`
  (boot 466fd5ea…, system 76bbf8b4…). **Do not delete it.** The owner asked for the SD card and work folder to be cleaned, but the permission system blocked bulk deletion; see §7.
* Recovery request mechanism: Android's `adb reboot recovery` does NOT enter TWRP on this ROM. `tools/flash-release.ps1` writes the BCB itself.

## 2. Installable releases (all built from the shared source tree)
| ZIP | Content | Status |
|---|---|---|
| `kyf37-rom/…twrp-v13.zip` | boot animation v2, Home grid, quick keys etc. | flashed + tested earlier (boots in ~90 s) |
| `…twrp-v14.zip` | + microG, Wi-Fi supplicant rc, camera libs/stubs, cpuset, settings app, sounds, wallpaper, user boot animation (sha fdaf4860…) | built, **never flashed** |
| `…twrp-v15.zip` (sha c6f6cfe4…0319) | v14 + Aurora Store 4.8.4 | built, signed, installer-verified offline, **never flashed** |
| later | radio/GPU/TV changes are in the tree **but no zip contains them** | §4, §5, §6 |

Pipeline (details in AGENTS.md §3): `build-locked.sh` → `package-release.sh vN` → `sign-rom-boot.py` → `build-twrp-android10-installer.py vN` → `tools/flash-release.ps1 <zip>`.
Revision names by owner: lead v14–v19 (the owner said "do not create v16" during the TV task; v16 is unused), radio v20–v29, gpu v30–v39, tv v40–v49.
The installer script has revision tuples and a vendor-ELF count gate (`177` for v14/v15; the radio fixes add libraries → raise it) — see that script.
**System partition is nearly full** (tree ≈1358–1370 MB of 1538 MB). GmsCore was ABI-stripped (only armeabi-v7a, re-signed by the build with testkey) to fit.

### What the lead did this session (all scripted under `device-inspection/`)
side-key shade (`fix-android10-side-key-shade.py`), compact soft-key bar (`…compact-softkeys.py`), lid-open answers calls (`…lid-answer.py`), End key = Home (`…endcall-home.py`),
icon-grid launcher `Kyf37Home` + quick keys `Kyf37QuickKeys` (`…quick-keys.py`, doc `KEYPAD.md`), Phone settings app (`…phone-settings-app.py`), disable "built for older Android" dialog (`…no-old-app-dialog.py`),
original ringtones (`…oem-sounds.py`), default wallpaper (overlay `drawable-nodpi/default_wallpaper.png`), boot animations, microG (`install-microg.py`, `MICROG.md`), Aurora Store (`install-aurora-store.py`),
camera fixes (`…camera-cipo-libs.py`, `…camera-kc-api.py`, `build-kyocera-compat-dex.py` + `patch-kyocera-compat-smali.py`, `port-stock-apps-android10.py`), cpuset (`…cpuset-and-fbbuffers.py`),
Wi-Fi supplicant (`…wifi-supplicant.py`, `…remove-legacy-supplicant.py`), TV integration (`install-tv-oneseg.py`, `check-tv-integration.py`, `TV.md`).
Verified on hardware: side-key shade, soft-key bar, Home grid, Contacts quick key, boot of v10–v13, `wlan0` appears, one camera enumerates after provider restart.
Not hardware-verified: everything else listed above (it was only built).

## 3. Open owner requests (status)
1. Settings app for keypad — built (`Kyf37PhoneSettings`), untested on phone.
2. Original ringtones/navigation sounds — ringtones/notifications/alarms wired (`audio-oem-sounds.mk`, defaults 02_rt / 03_nt / 01_al_alarm01); navigation (UI) sounds were already in the ROM; check `ro.config.*` actually won over Lineage's `Orion.ogg` after a flash.
3. Default wallpaper — done in source (480x854 from `Downloads/wallpaper.png`).
4. Boot animation — currently `Downloads/bootanimation.zip` (sha fdaf4860…4106). The owner replaced it twice; always use the newest file they name.
5. microG + Aurora — done in source (see MICROG.md). First boot with microG is the risk: priv-app allowlist is generated from manifests; a missing permission → system_server crash loop (boot stuck on logo). Recovery: add the permission to `privapp-permissions-microg.xml` (rebuild) or, live, push an xml to `/system/etc/permissions` after `clear-system-temp-wp`.
6. Camera — see §6.
7. Tearing — **unfixed**, see §5.
8. Wi-Fi + cellular — **Wi-Fi is SOLVED & HARDWARE-VERIFIED** (connected to `<home-ap>`, DHCP 192.168.1.170, DNS/ping/curl ok, Android `Score{60} everValidated{true}`, see §4). Cellular still blocked (see §4).
9. "Fix the GPU, newer Adreno driver and Linux kernel" — researched: mainline msm8909 kernel (postmarketOS 6.12) lacks Adreno 304, audio, modem, camera ⇒ not viable. A CAF msm-3.18 vendor kernel would need all Kyocera drivers forward-ported (weeks). Newer Adreno blobs (Android 8.1-era) need a kgsl ioctl missing in 3.10 (gpu agent finding). Not attempted.
10. Japanese TV (One Seg) — integration done in source; **making it actually run is open (§8)**; the owner's latest request: "resolve the symbols so that it works like in the original ROM".
11. Clean work folder + SD card — pending permission (§7).

## 4. Radio agent results (see `RADIO.md`)
* **Wi-Fi**: **SOLVED and VERIFIED live on hardware (2026-10-08)**. Connected to live AP `<home-ap>` (WPA2-PSK), 4-way handshake ok, acquired DHCP IP `192.168.1.170/24`, gateway ping ok, DNS resolved `google.com`, ping `8.8.8.8` (0% loss, 22 ms avg), curl `https://www.google.com` returned `HTTP/1.1 200 OK`, Android framework marked network `VALIDATED` (`Score{60}`, solid Wi-Fi icon). Three root causes fixed:
  1. `wpa_supplicant` deadlock: `roaming_vendor_cmd_avail=0` in `driver_nl80211_capa.c` and `error_handler` returning `NL_STOP` in `driver_nl80211.c` (`fix-android10-wpa-supplicant-hang.py`).
  2. `NL80211_CMD_CONNECT` -ERANGE (-34): attribute ID 204 collision between Android 10 UAPI (`NL80211_ATTR_SOCKET_OWNER`, flag len 0) and Linux 3.10 CAF kernel (`NL80211_ATTR_AUTHORIZATION_STATUS`, NLA_U8 minlen 1); disabled in `driver_nl80211.c` (`fix-android10-wpa-supplicant-hang.py`).
  3. Default route -ENETUNREACH (-101): Linux 3.10 `fib_check_nh` with `flowi4_iif=0` failed policy routing rules; fixed by adding `RTNH_F_ONLINK` to IPv4 gateway routes in `system/netd/server/RouteController.cpp` (`fix-android10-netd-onlink.py`).
* rild: crash cause = stock `libperipheral_client.so` (Android 5 C++ Binder client) corrupts its interface pointer on Android 10 (SIGSEGV 0x20300868); the sibling `libpm_client_a10` makes `pm-service` crash too. Fix: `libpmstub_kyf37.so` (5 `pm_client_*` functions, no Binder) with `libril-qc-qmi-1.so` repointed. rild now stays up, IRadio 1.0/1.1 + ISap register. qseecomd fixed by adding `librpmb.so`, `libssd.so`, `libdrmtime.so`.
* **Cellular still blocked:** the modem boots and answers DMS but its SMD channel table has no `DATA5_CNTL` (`/dev/smdcntl0`), so no QMI/SIM/data/calls. Hypotheses: modem EFS state changed since stock; missing stock pieces (`dpmd`, `cnd`, `ssr_setup`). **Decision needed:** restoring `modemst1/modemst2` from `phone-backup/` would be a modem-partition write — the agent did NOT do it. Treat as owner-approval-required and keep backups.
* Hazards: panics/hard resets from `cat` on the mdss debugfs `base_reg`/`panel_reg`, `dd` on `/dev/mem` above low RAM, and DIAG mask commands to the modem. `/proc/last_kmsg` is the best crash tool.
* The agent's changes landed after v15 → **no zip contains them.** Next zip should be v20 (radio's name) or v16+ per owner choice; raise the vendor-audit count gate and add revision to the installer tuples.

## 5. GPU agent results (see `GPU.md`, agent was stopped by the owner)
* Measured on the phone: `DMA_P_IBUF_ADDR` is latched at start-of-frame; buffers are never reused while scanned; no MDP underflow under load; vsync is a clean 60 Hz (16.66 ms). So buffer timing, bandwidth and refresh are **not** the cause of the owner's tearing.
* Built, untested on hardware: S1 uncached framebuffer buffers (`fix-android10-gpu-fb-uncached.py`, property `persist.kyf37.fb_uncached`, default 1), zram swap 384 MB (`fix-android10-gpu-memory-perf.py`, `init.kyf37.gpu.rc`; v13 had **no swap**), fb0 test tool `device-inspection/gpu/fbtear` (white bar flipped directly on fb0 with SurfaceFlinger stopped: if clean there but tearing under Android ⇒ SF/GPU/HWC/ION; if tearing there too ⇒ panel/DSI/kernel).
* Remaining suspects: cached ION buffers vs stock's uncached fb0, DSI/panel-side errors, judder perceived as tearing. Needs the owner's eyes. Tried without success earlier: forced client composition, `glFinish` in RenderEngine, HWC sync-wait flag, partial-update off.
* Also: CPU hotplug (core_ctl) leaves CPU0/2 offline when idle (normal), JIT is off (`dalvik.vm.usejit=false` in the release rc, a perf cost), GPU idles at 307 MHz.

## 6. Camera state
* Hardware path works up to the app: sensor OV8856 + actuator + EEPROM load; "aec init failed" was caused by missing `libCipo_ae.so`/`libCipo_awb.so` (fixed in source and pushed live); boot-order bug (provider enumerates before `mm-qcamera-daemon` → 0 cameras) fixed by `init.kyf37.camera.rc` (restart provider 4 s after `qcamerasvr` runs).
* Original Kyocera Camera app needs stock framework pieces: `jp.kyocera.kcfp.*` helper classes (bundled as `classes2.dex` via `kyocera-compat.dex`, Kyocera-only widget/window calls turned into `nop`) and Kyocera extensions of `android.hardware.Camera` (stubs added to framework `Camera.java`: 4 callback interfaces + 11 methods). After those, the app started (`CameraApplication` ok); the next failure seen was `NoClassDefFoundError: android.hardware.Camera$AutoSceneCallback` — **that is what the framework stubs fix, but they were never run on a phone** (needs a rebuild+flash; framework change).
* No preview/photo has been seen yet. Test with `monkey -p jp.kyocera.camera -c android.intent.category.LAUNCHER 1` (launching the activity without the MAIN action NPEs in the app).
* Flashlight (`jp.kyocera.mobilelight`) likely needs the working Camera HAL/torch; untested.
* To retest a ported APK without a reflash: `device-inspection/sign-test-apk.sh in out` then `adb install -r -d`.

## 7. Pending permissions / decisions (do not do these silently)
* **Cleanup (owner requested, blocked by the permission system):** SD card — delete rollback folders `KYF37-Android10-rollback-19691231-190334-267`, `…193251-294`, `…193534-254`, `…20171130-184415-269`, `…185051-277`, `…192630-273`, `…194930-265`, `…201314-265` (more were created later; list with `ls /external_sd`), `KYF37-v8-before-v9-kernel-test`, `kyf37-rom-20261007` (old Android 7 raw system), `kyf37-v3-boot-before-kernel-test.img`, old zips v1.disabled/v5/v6/v7/v8/v10(/v11/v12 once superseded). **Keep:** `…19691231-191652-367` (stock), `TWRP/`, `kyf37-download-triggers-disabled`, `kyf37-sddl-recovery-request-backup`, `Android/`, `LISMO/`. Work folder: old `kyf37-rom/android10-go-candidate-*` folders appear to have been removed already; do not delete `phone-backup/`, `device-inspection/system-stock.img`, `kyf37-twrp-device/`, `tools/`.
* **Modem partition restore** (`modemst1/2` from `phone-backup/`) only with explicit owner approval; read-only analysis first.
* Owner keeps asking not to be asked questions; where a decision is irreversible (deletion, modem writes), still state it clearly.

## 8. One Seg TV — the task in progress when this file was written
Goal (owner): "resolve the symbols so that it works like in the original ROM".
Integration already in the tree (see `TV.md`): `FsDtvApp` (platform-signed), `Kyf37Tv` launcher (starts `dtvserver` via `ctl.start`), `dtvserver` + 15 libs in `/system/lib`, `media/dtv`, `public.libraries-kyocera.txt`,
`dtvserver` set to on-demand in `ramdisk/init.kc.common.rc`. Static check `device-inspection/check-tv-integration.py` passes. **No build including it succeeded yet** (a duplicate `wpa_supplicant.conf` rule from the radio agent broke the shared build; the radio agent says it removed it — re-run `build-locked.sh` to confirm).

**Unresolved imports (62 refs, 58 distinct), from `modem-investigation/tv-tuner/native-compatibility-audit.json` (v13 image):**
* `libDtv.so` (5): `android::GraphicBuffer::GraphicBuffer(ANativeWindowBuffer*, bool)` (removed in Android 8), `ucnv_close_53`, `ucnv_fromUChars_53`, `ucnv_open_53`, `ucnv_toUChars_53`.
* `dtvserver` (8): `u_memset_53 u_strcat_53 u_strcpy_53 u_strlen_53 ucnv_close_53 ucnv_fromUChars_53 ucnv_open_53 ucnv_toUChars_53`.
* `libDtvULayer.so` (49): Skia (`SkPaint` setters, `SkTypeface::CreateFromFile`, `SkImageDecoder::DecodeMemory`, `SkBitmap`, `SkCanvas` draw/clip/rotate/translate/readPixels), `android::AudioTrack` old API (`setSampleRate stop flush start write setVolume stopped` + the long-form constructor), `GraphicBufferMapper::lock(native_handle const*, int, Rect const&, void**)` (4-arg old signature), and missing library `libskia.so`.
Everything else in the stack resolves by name.

**My analysis (unverified assumptions flagged):**
1. Name resolution is only the first layer. The stack is Android 5 C++ code: `dtvserver`/`libDtvService` (BnInterface-derived Binder service) and `libDtv` (BpInterface client loaded into the app by `libDtv_jni`). The radio agent proved on this device that an Android 5 C++ Binder *client* (`libperipheral_client`) corrupts its interface pointer when linked against Android 10 `libbinder` (IInterface/`asBinder` ABI change). Expect the same for TV. Also Android 10's `Parcel::writeInterfaceToken` adds a work-source int and header magic that Android 5 readers do not expect — mixing one side Android 5 libbinder and the other Android 10 will mis-parse; both sides must use the same Parcel implementation. (Unverified: exact servicemanager protocol on this build; check `frameworks/native/cmds/servicemanager` in the tree.)
2. ICU `_53`: Android 10 exposes ICU in `libicuuc.so` (runtime APEX, versioned names such as `_63`/`_64`). Provide a shim `libdtvcompat.so` exporting `u_*_53`/`ucnv_*_53` that forwards via `dlsym` to the versioned symbols (probe suffixes 56–70); `u_memset/strcat/strcpy/strlen` can be implemented directly. Low risk; also needed by the stock Skia if used.
3. Skia: Android 10 has no public/standalone Skia. Options: (a) ship the stock Android 5 `libskia.so` (+ `libft2.so`, `libpng`, `libjpeg`, `libexpat`, ICU shim) as a private copy under a private directory, patching `DT_NEEDED`, so `libDtvULayer` behaves as on stock; (b) implement the ~25 used entry points on a small software rasterizer. (a) preserves original rendering; check dependency closure with the same audit script (`prepare-stock-tv-windows.py`, `image_reader.py`).
4. AudioTrack/GraphicBufferMapper/GraphicBuffer: the old C++ constructors/methods change object layout. Prefer adapter functions in the shim that allocate **Android 10 objects themselves** (opaque handles) rather than letting old code `new` an Android 10 class with an Android 5 `sizeof`; or move audio to AAudio/OpenSL and video to ANativeWindow/AHardwareBuffer inside a rewritten `libDtvULayer` surface (this is the "carefully specified backend" the README proposes; the low-level `libdtvtuner.so` has no missing imports).
5. The most robust but largest approach is a **private Android 5 userland for the TV daemon** (Android 5 `libbinder/libutils/libcutils/libui/libgui/libmedia/libskia/libicuuc` in `/system/lib/dtv-compat/`, loaded with `LD_LIBRARY_PATH` for `dtvserver`, with the daemon registering in a way the Android 10 servicemanager accepts) plus a matching client stack for the app. Binder compatibility between an Android 5 server and an Android 10 app process is the hard part — test with a minimal client first.
6. Unknown: whether `dtvserver` needs `/dev/dtvtuner_pm0` open permanently (README: closing the handle powers the tuner off); `RecordDataIF` optional `libdtvsdserver_jni.so` is absent (recording off). Spain broadcasts DVB-T, so even a perfect port will show no stations; success criterion is "app starts, daemon starts, tuner node opens/powers, scan runs and fails gracefully" — keep thermal protections, never leave the tuner powered, avoid boot-time scans.
7. Hardware safety for tests: do not poll or leave the tuner on; stop `dtvserver` after each experiment (`adb shell stop dtvserver`); hold the phone lock; never read mdss debugfs panel/base registers.

**Suggested next steps for the TV work**
1. Rebuild (`build-locked.sh`) to prove the integration compiles and fits; flash a zip (v40 if the TV agent does it) and run the launcher's check (key 2).
2. Write `device/kyocera/kyf37/dtvcompat/` (Android.bp `cc_library_shared`, 32-bit): ICU53 forwarders first; get `dtvserver` to *start* (`start dtvserver`, `logcat`, tombstones) before touching Skia.
3. Then Skia/AudioTrack/GraphicBuffer adapters or the private-A5-libs route; verify with `native-compatibility-audit.json`-style audits (the audit helper scripts live in `modem-investigation/tv-tuner/`).
4. Validate Binder both directions with a tiny test client before running the full app.
5. Document every experiment (including failures) in `TV.md`.

## 9. Pitfalls recap (more in AGENTS.md §4)
* Git Bash rewrites `/…` arguments → always `export MSYS_NO_PATHCONV=1` or use PowerShell.
* `/system` is eMMC write-protected in Android: `adb push device-inspection/clear-system-temp-wp /data/local/tmp/` then run it with `--clear-system-temporary` before remount rw.
* `adb root` restarts adbd; wait 4 s. `adb reboot recovery` doesn't work; use `tools/flash-release.ps1`.
* If TWRP "bootloops": corrupted `/data` + `errors=panic`; use `device-inspection/fastcap.py` and `fsck-race.py` (AGENTS.md §4).
* A stale `.orig/.rej` file inside `frameworks/base/core/res/res/values/` breaks the resource build (a `patch` leftover once cost a build).
* Only one soong build at a time; use `build-locked.sh`. WSL can time out under heavy load (`Wsl/Service/0x8007274c`) — retry.
* The owner signing key (`kyf37-twrp-device/owner-signing-key.pem`) must never be printed, copied or uploaded.

## 10. Offline modem/LTE work (no phone), added at the end of the session
Tools added: `modem-investigation/fix/disasm_annotate.py` (Capstone Thumb disassembler with string xrefs; `pip install capstone pyelftools` on Windows Python), `modem-investigation/fix/diff_services.py` (stock-vs-ROM init service diff, run in WSL).
Findings:
* Stock `pm-service` state enum (from its disassembly): 0 going off-line, 1 off-line, 2 going on-line, 3 on-line. Power on = `open(/dev/subsys_<name>)`, power off = `close(fd)`; one vote count per peripheral. Its startup does NOT power the modem; only a vote does. "voter did not reregister after crash. Powering down" means a crashed voter makes it power the modem down.
* Hypothesis (unverified): old rild crashes while voting made pm-service power the modem down (DMS mode 5); with the radio agent's stub nothing ever votes. A proper Android-10 pm-service replacement + real client (`modem-investigation/fix/pm_client.cpp`, protocol documented in its header and `REPORT-MODEM-LTE.md`) would restore stock behaviour; never power down on zero votes. NOT written yet. Plan: one library with a property switch (`persist.kyf37.pm.real`) between stub and real client; new `pm-service` registering `vendor.qcom.PeripheralManager`, descriptors/transactions as in pm_client.cpp, notify via oneway transact code 1 with the state number as event.
* Services in the stock ramdisk missing from the ROM (not disabled in stock): `ssr_setup` (tiny, deps libc/libcutils/libmdmdetect/libutils — safe to add; sets restart_level from `persist.sys.ssr.restart_level`), `dpmd`, `cnd`, `ATFWD-daemon` (Binder/QMI based, riskier), Kyocera `kuartd kdfs kerrd lkspad initwork usb_init`. None obviously creates SMD `DATA5_CNTL`; root cause of the missing channel is still OPEN.
* Best remaining experiment needs the phone: the TWRP control test with stock daemons (see RADIO.md §4). No v16 radio zip was built.
