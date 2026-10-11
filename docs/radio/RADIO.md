# RADIO.md - Wi-Fi and cellular (radio agent), 2026-10-08

Status legend: VERIFIED = seen on the phone; BUILT = compiles only; OPEN = not solved.

## 1. Status

| Item | Status | Notes |
|---|---|---|
| wlan0 driver/firmware (rebuilt prima `wlan.ko`) | VERIFIED | firmware loads, MAC 6c:76:60:.. (Kyocera OUI), 2.4 GHz only. The old "WDI status 38" did not reproduce; stock driver swap not needed |
| Wi-Fi association / DHCP / Internet | VERIFIED live | 2026-10-08 21:40 CEST: Connected to `<home-ap>`, 4-way WPA2 handshake ok, IP 192.168.1.170, DNS / ping 8.8.8.8 / google.com ok (0% loss, ~22 ms), curl HTTPS 200 OK, Android framework `VALIDATED`. See section 2. |
| SoftAP / P2P / tethering | NOT TESTED | p2p0 exists, hostapd HAL present |
| rild stays alive, IRadio 1.0/1.1 + ISap registered | VERIFIED live | with the PM stub (section 3) |
| qseecomd stays alive | VERIFIED live | needed `librpmb.so`, `libssd.so` |
| Modem boots (MPSS JO.1.0.c5.8, Nov 2018), DMS answers over IPC router | VERIFIED | DMS op-mode reads 5 (SHUTTING_DOWN) |
| `/dev/smdcntl0` (SMD DATA5_CNTL) / QMUX / NAS / SIM / data / calls / SMS | OPEN | modem never allocates DATA5_CNTL (section 4). No SIM-state test possible |

## 2. Wi-Fi

Findings / commands:
* v13 ramdisk still defines legacy `wpa_supplicant`/`p2p_supplicant` (v14+ ramdisk removed them). To test live on v13: put a shim script at `/system/bin/wpa_supplicant` (`exec /vendor/bin/hw/wpa_supplicant -O/data/vendor/wifi/wpa/sockets -puse_p2p_group_interface=1 -dd -g@android:wpa_wlan0`), `svc wifi enable`, `start wpa_supplicant`. (init supplies the abstract-socket fd; running the binary by hand fails with "Failed to open Android control socket".)
* Failure was `SupplicantStaIfaceHal: Failed to create ISupplicantIface 1`. Supplicant log showed "P2P: initialized" on wlan0 -> `isP2pIface()` true -> iface registered as P2P. Fix: `/vendor/etc/wifi/wpa_supplicant_overlay.conf` = `disable_scan_offload=1 / p2p_disabled=1 / tdls_external_control=1`. After that "Successfully setup Iface wlan0 STA", scanner works.
* `/vendor/etc/wifi/*` had only ever been pushed by hand; no build rule installed them. `wpa_supplicant.conf` is installed by the wpa_supplicant module (my copy rule for it broke the build and was removed).
* Country: `ro.boot.wificountrycode=ES` added (property read by WifiInjector).
* Script: `device-inspection/fix-android10-radio-wifi.py` (idempotent).
* `svc wifi disable/enable` unloads/reloads the driver (HAL), normal.

### Wi-Fi Association & Network Validation Fixes (2026-10-08 21:40 CEST) — SOLVED & VERIFIED

Full WPA2-PSK connection, DHCP lease, DNS resolution, internet ping, HTTPS curl, and Android network validation (`Score{60}`, `everValidated{true}`) are **VERIFIED on live hardware**. Three separate compatibility issues had to be resolved:

1. **Supplicant Hang on Vendor Commands (`roaming_vendor_cmd_avail`)**:
   - *Symptom*: Calling `wpa_driver_nl80211_set_bssid_blacklist` or roaming vendor subcommands caused `wpa_supplicant` to hang indefinitely, blocking all association events and CLI commands.
   - *Root cause*: `driver_nl80211_capa.c` probed `QCA_NL80211_VENDOR_SUBCMD_ROAMING` and set `drv->roaming_vendor_cmd_avail = 1`. The prima kernel driver (`wlan.ko`) rejected this vendor subcmd. In `driver_nl80211.c`, `error_handler` returned `NL_SKIP`. Libnl-genl interprets `NL_SKIP` by continuing to wait for an ACK/msg, resulting in an infinite poll deadlock.
   - *Fix*: In `external/wpa_supplicant_8/src/drivers/driver_nl80211_capa.c`, set `drv->roaming_vendor_cmd_avail = 0`. In `driver_nl80211.c`, patched `error_handler` to return `NL_STOP` and ensure `*ret` is negative.

2. **Kernel Connect Rejection with `-ERANGE` (-34)**:
   - *Symptom*: When attempting to associate with an AP, `wpa_supplicant` reported:
     `nl80211: MLME connect failed: ret=-34 (Numerical result out of range)`.
   - *Root cause*: Attribute ID 204 collision between modern Android 10 UAPI and Linux 3.10 CAF kernel:
     - Android 10 `nl80211_copy.h`: attribute 204 is `NL80211_ATTR_SOCKET_OWNER` (`NLA_FLAG`, length 0).
     - Linux 3.10 CAF `net/wireless/nl80211.c:nl80211_policy`: attribute 204 is `NL80211_ATTR_AUTHORIZATION_STATUS` (`NLA_U8`, `minlen = 1`).
     - In `driver_nl80211.c:nl80211_connect_common`, `nla_put_flag(msg, NL80211_ATTR_IFACE_SOCKET_OWNER)` was sent unconditionally. Kernel `lib/nlattr.c:validate_nla` evaluated `attrlen (0) < minlen (1)` and returned `-ERANGE` (-34) during generic netlink policy validation, aborting `NL80211_CMD_CONNECT` before the prima driver was ever called!
   - *Fix*: In `external/wpa_supplicant_8/src/drivers/driver_nl80211.c:nl80211_connect_common`, commented out `nla_put_flag(msg, NL80211_ATTR_IFACE_SOCKET_OWNER)`.
   - *Script*: `device-inspection/fix-android10-wpa-supplicant-hang.py` (idempotent).

3. **Linux 3.10 Gateway Policy Routing (`Network is unreachable` / -101)**:
   - *Symptom*: `wlan0` acquired IP `192.168.1.170/24` via DHCP, but `netd` failed to install the default route into `table wlan0`, and manual `ip route add default via 192.168.1.1 dev wlan0 table wlan0` failed with `RTNETLINK answers: Network is unreachable`.
   - *Root cause*: In Linux 3.10 `net/ipv4/fib_semantics.c:fib_check_nh`, resolving a gateway route without the `RTNH_F_ONLINK` flag triggers `fib_lookup` with `flowi4_iif = 0`. Android's policy routing rules (`ip rule`) specify `iif lo` on all interface-specific tables. Because `flowi4_iif = 0` does not match `iif lo`, the lookup misses all routing tables and falls through to rule 32000 (`unreachable`), returning `-ENETUNREACH` (-101).
   - *Fix*: In `system/netd/server/RouteController.cpp:modifyIpRoute`, added `.rtm_flags = static_cast<unsigned int>((family == AF_INET && nexthop && interface != OIF_NONE) ? RTNH_F_ONLINK : 0);`. This sets `RTNH_F_ONLINK` on IPv4 default gateway routes so the 3.10 kernel verifies gateway reachability directly on the interface without the failing `fib_lookup`.
   - *Script*: `device-inspection/fix-android10-netd-onlink.py` (idempotent).

**Verification on live phone**:
- Connected to `<home-ap>` (BSSID `xx:xx:xx:xx:xx:xx`, -39 dBm).
- 4-way WPA2-PSK handshake completed (`PTK=CCMP GTK=CCMP`).
- IP assigned: `192.168.1.170/24`, default route: `default via 192.168.1.1 dev wlan0 table wlan0 proto static onlink`.
- Ping gateway `192.168.1.1`: 0% loss, ~12 ms.
- Ping Google DNS `8.8.8.8`: 3/3, 0% loss, ~22 ms.
- DNS resolution + ping `google.com`: 3/3, 0% loss, ~24 ms.
- `curl -sI https://www.google.com`: `HTTP/1.1 200 OK`.
- `dumpsys connectivity`: `Score{60} everValidated{true} lastValidated{true} Capabilities: ... VALIDATED ... SSID: "<home-ap>"`.
- Status bar display: Solid Wi-Fi icon with internet access verified.


## 3. rild crash (SIGSEGV 0x20300868)

Root cause: stock `libperipheral_client.so` (Android 5 C++ Binder objects) corrupts its own interface pointer on Android 10 (see also `modem-investigation/REPORT-MODEM-LTE.md`). Additional finding (live): the **server side is broken the same way**. With the sibling `libpm_client_a10` (real wire protocol) rild registers and votes, `pm-service` logs "QCRIL voting for modem / modem new state: going on-line" and then dies with SIGSEGV (no tombstone: pm-service blocks signals and is non-dumpable; core dump parsed with `radio-work/parsecore.py`: fault at pm-service+0x4b38, in the loop that notifies each client callback). So replacing only the client library is not enough; init respawns pm-service and every vote kills it again.

Fix shipped: `libpmstub_kyf37.so` (`third-party/radio/pm_client_stub.c`) - the five `pm_client_*` functions, no Binder; `libril-qc-qmi-1.so` DT_NEEDED repointed to it. Justification: the MSM8909 modem is booted by the kernel (pil-q6v5-mss at ~5.8 s), pm-service/PM voting only matters for airplane-mode power-off. This overrides `fix-android10-pm-client.py` (libpm_client_a10 stays in the tree unused). Script: `device-inspection/fix-android10-radio-rild.py` (also installs `librpmb.so`, `libssd.so`, `libdrmtime.so` from the stock image for qseecomd).

Also missing in the ROM vs stock and pushed live (NOT yet scripted into the tree; do next): `/system/etc/data/{qmi_config,dsi_config,netmgr_config}.xml` (needed by qmuxd/dsi_netctrl/netmgrd for mobile data), `/system/etc/sec_config` (irsc_util IPC security rules). Sources: `~/kyf37-rom/stock-system/etc/`.

## 4. Why no QMI / SIM yet (OPEN)

Evidence:
* Modem alive: PIL OK, SSCTL up, rmt_storage serves modem_fs1/2, tftp WRQ ok, IPC-router DMS (svc 2) works via `third-party/radio/qmi_ipc` (`qmi_ipc 2 1 2d` = operating mode -> 5; `... 2e 01010000` sets ONLINE, accepted, no effect).
* SMD channel table from the modem has only DS, IPCRTR, SSM_RTR_MODEM_APPS, sys_mon, DIAG*, apr_*, DATA1-4, DATA11 - **no DATA5_CNTL, DATA40_CNTL, BAM_DMUX_CTL**. qmuxd (needs smdcntl0) blocks in `smd_pkt_open` (-110). NAS(3)/WDS/WMS/UIM/VOICE are not on the IPC router either (the repo's old notes say that was also true on stock; stock used QMUX).
* Same result after clean modem SSR (`echo RELATED > /sys/bus/msm_subsys/devices/subsys2/restart_level; echo restart > /sys/kernel/debug/msm_subsys/modem`), with pm-service/rild/qmuxd stopped, with qseecomd fixed. So not pm-service, not qseecomd, not rild.
* Userspace daemons/ramdisk are the same as stock; kernel is the OEM source. OEM-kernel + Android10 userspace (older v5/v6 logs) also never got DATA5_CNTL. Stock Android 5 did (old LTE-band QMUX work in HANDOFF/STATUS.md).
* Not yet ruled out: modem EFS (modemst1/2) state changed since stock; a stock-only userspace item (candidates missing from ROM: `dpmd`/`cnd`, `ssr_setup`, `port-bridge`, `wdsdaemon`, `sec_config`, `/system/etc/data`); something in Android 10 bionic vs stock daemons.
* Control experiment started: TWRP (OEM kernel, Android 5.1 bionic, BCB trick from `tools/flash-release.ps1`) - the modem does boot there if you `mount modem /firmware` and `cat /dev/subsys_modem` (error is harmless, kernel boots it; 'Brought out of reset'). Next step was to run the **stock daemons** (rmt_storage, tftp_server, qseecomd, time_daemon, irsc_util, qmuxd + stock libs, tmpfs at /system with `/system/rfs` links) inside TWRP and check `/sys/kernel/debug/smd/ch` for DATA5_CNTL. If it appears -> Android 10 userspace is at fault; if not -> modem NV/EFS state (owner decision: restoring modemst from `phone-backup` would be a modem-partition write, which I did not do).

## 5. Hazards found (do not repeat)

* Panics/hard resets: `cat` of the mdss panel debugfs `base_reg`; `dd` of `/dev/mem` above lowmem (read_mem oops); sending DIAG msg-mask commands (`diag_min`, QCSuper bridge) -> "Unable to send msg masks to peripheral 0" then oops in `msm_bus_dbg_client_data` (irq/..cpu-bwmon) or silent reset. `/proc/last_kmsg` holds the previous boot's full kernel log and is the best crash tool. restart_level is SYSTEM, so any modem/wcnss crash resets the phone.
* `adb reboot recovery` does not enter TWRP on this ROM (use the BCB write in `tools/flash-release.ps1`).
* `qseecomd` crash-loop (status 255) before the fix; `dmesg` drains into logd, boot logs only via last_kmsg.

## 6. Reproduce / tools

`third-party/radio/`: `qmi_ipc` (QMI over IPC router), `libpmstub_kyf37.so` + `build-pm-stub.sh`, `diag_min`/`diagf3.py` (DIAG; crashes the phone, do not use), README with provenance. Work files in `radio-work/` (tombstone, last_kmsg logs, disassembly; contains partition carve-outs `carve/` - private, do not publish).
Live /system edits: `clear-system-temp-wp --clear-system-temporary`, `mount -o remount,rw /system`.

## 7. Next steps

1. Finish TWRP stock-daemon control test (section 4). 2. Script `/system/etc/data`, `sec_config`. 3. Build + zip v20 (needs lead's build slot; the previous Makefile conflict is fixed). 4. [DONE] Wi-Fi association and internet validation verified live on `<home-ap>`.


## 8. Update 2026-10-09 (Claude, lead session): controlled experiments on the missing DATA5_CNTL

Everything below is MEASURED. Result: **the modem is not fixed yet**; the Android 10 userspace and our kernel build are now ruled out as the cause.

| Experiment | Result |
|---|---|
| `qseecomd` on Android 10 | had been crash-looping (`dlopen(librpmb.so) failed -> RPMB_INIT failed`): `librpmb/libssd/libdrmtime` were **not in the running v17 image** (earlier live pushes did not persist). Installed live; `qseecomd` now runs its time + file-system listeners (missing only `libfwlock`, keymaster app). Modem SSR afterwards: **no change** |
| DMS over IPC router | works: IMEI `<IMEI>`, caps GSM/UMTS/LTE/TDS. Operating mode was **5 (shutting down)**; set LPM then ONLINE works (mode becomes 0) but NAS/UIM/WMS/VOICE/WDS never register and no `DATA5_CNTL` appears |
| Stock kernel config vs ours (`extract-ikconfig` of the owner's stock `boot.img`) | identical for all modem/SMD/PIL/IPC options (34 diffs, all Android-10 cgroup/ACL/sdcardfs/memfd related). Command line identical to stock incl. `androidboot.mode=kcpermissive` |
| **TWRP control** (stock kernel binary + stock daemons rmt_storage/tftp_server/time_daemon/qseecomd on a tmpfs /system built from the stock image; modem held up via an open fd on `/dev/subsys_modem`, which the kernel needs or it shuts the modem down on close) | modem reaches the **identical** state: the same 20 router services, only `DATA1-4`,`DATA11` channels, no `DATA5_CNTL`. Adding stock `dpmd`, `ssr_setup`, `qcom-system-daemon`: no change |
| Modem firmware partition `modem` (p1) | bit-identical to the owner's original backup (sha256 2c6ec744...) |
| `modemst1/2` EFS | restored the owner's pristine copies (`radio-work/carve/`, verified by hash), then re-ran the control: **no change**. (Fresh pre-restore copies kept in `radio-work/backup-20261009/`; the modem has since rewritten the partitions, as normal) |
| `fsg/fsc/ssd/sec/misc` | identical to original. `dnand` differs only in Kyocera's log area. `/persist/rfs` identical in content |
| Clock set to 2019 in the control | no change (RTC unset in TWRP anyway) |
| `rmt_storage`/`tftp_server` traces during modem boot | modem reads and later rewrites its EFS; tftp only handles `server_check.txt`: no failed file requests |

What this means: with firmware, EFS, kernel, command line and the stock daemons all equal to the original, the modem still does not bring up its data/NAS stack. The remaining differences from the day stock QMUX worked (2026-10-06) are things outside the phone's storage: **a SIM card in the slot** (stock-era NAS band read/write over `qmuxd` was recorded; whether a SIM was installed then is not documented), and the stock Android 5.1 userspace as a whole (Kyocera daemons such as `initwork`, `kdmd`, `kerrd`, `kuartd`, which the ROM lacks but none of which reference the modem beyond SSR settings).
Decisive next experiments (not done): (1) test with a SIM inserted; (2) boot the stock rollback (`KYF37-Android10-rollback-*`, stock boot+system) to see whether stock still brings QMUX up today (needs care: Android 10 userdata under 5.1).
Also shipped now (source tree, rebuild needed): `fix-android10-radio-etc.py` adds `/system/etc/data/*.xml` and `/system/etc/sec_config`; `fix-android10-radio-rild.py` already ships `librpmb/libssd/libdrmtime`.


## 9. Update 2026-10-09 evening (radio-cell agent): stock baseline attempt - PHONE LEFT UNREACHABLE, owner action needed

Goal: make the modem register (emergency-only is enough) and enable Spanish LTE bands. **Not achieved. The phone is currently not enumerating on USB.**

What was measured (Android 10, kernel #17, before the baseline attempt)
* Modem channel table unchanged: only DS, IPCRTR, SSM_RTR_MODEM_APPS, sys_mon, DIAG*, DATA1-4/11; no DATA5_CNTL; `/dev/smd0` exists but rild gets no NAS. SMSM apps state `0x1229`, modem `0x08008009`; smp2p modem<->apps handshake is complete (slave-kernel 0x6). rild/qmuxd/netmgrd/pm-service/time_daemon/rmt_storage/tftp_server/qseecomd all running; `gsm.version.baseband=909EAAAANVZM-1.169552...` (MPSS.JO.1.0.c5.8, build 2017-07-29); telephony.registry: OUT_OF_SERVICE, no NetworkRegistrationInfo.
* Stock userspace audit (stock-ramdisk rc + binaries): the Kyocera daemons missing from the ROM (`initwork`, `kdmd`, `kerrd`, `kuartd`, `kdfs`, `uimd` is present) do not touch the modem: initwork = log collection, kdmd = diag mode flag, kerrd = thermal/error logger (reads `/dev/kclog_smem`, `/dev/dnand_cdev`, can trigger "subsystem restart MODEM"), kuartd = `/dev/ttyHSL3` for felica, kdfs = crash script. Nothing in stock init*.rc writes modem sysfs besides the `subsystem_restart`/`pil_msa` tunables already replicated. So the **stock-userspace hypothesis is weak**.
* Modem firmware strings show Kyocera customisation inside the modem (`kc_smem_alloc` in bfss, `mmgsdi_kc_lib` SIM-lock "perso" with carrier type OVERSEA/VIRTUAL, `UIM_KC_NV_PERFECT_LOCK`, `/modemkc/log`, `SMEM_UICC_INFO`). The modem therefore shares SMEM items with Kyocera apps-side code; a missing apps-side/SMEM contribution or a SIM-lock/perso state is still an untested explanation for NAS not starting. The firmware FAT has `image/modem_pr/mcfg/configs/mcfg_sw/generic/{APAC,CHINA,EU,KOREA,NA,RUSSIA,SA,SEA,COMMON}` directories with **no files** and the policyman carrier XMLs contain "Full RAT / no China" rules.
* Band history (Android 5 stock, QMUX, 2026-10-06, `device-inspection/lte-*.txt`): NAS Get System Selection Preference returned LTE mask `0x02000001` (B1+B26, au/KDDI Japan factory preference); writing `0x0a0800c5` (B1,B3,B7,B8,B20,B26,B28) succeeded and persisted across reboot. The write goes to modem EFS (`modemst1/2`), which was later replaced with the pristine copy, so the Spanish mask is **not** active now. Hardware capability (DMS Get Band Capability / NAS 0x34 TLV 0x1a..) was never read; B38/B40 and B28 are unverified. Re-apply with `device-inspection/kyf37_qmux --enable-spain` once QMUX is alive (NAS service present).

What I did (and the mistake)
1. Phone was in TWRP. SD already held the previous agent's verified backups: `/external_sd/kycell/a10-boot.img` (== boot partition, sha 4ff6cbc6...) and `a10-system.img` (== first 632414208 bytes of system, sha 6aad86bb...).
2. Rebooted to Android 10: state as above (no registration).
3. Back to TWRP; copied stock `system-stock.img` (sha 76bbf8b4...) and stock `boot.img` (sha 466fd5ea...) to `/external_sd/kycell/stock-system.img|stock-boot.img`; cleared system temp-WP; wrote stock system and **verified full readback = stock hash**.
4. Wrote the stock boot with a plain `dd` **without running `clear-recovery-boot-temp-wp`**: the write was silently ignored (readback still the A10 boot hash 4ff6cbc6...). Then cleared misc and rebooted. Result: **Android 10 kernel/ramdisk + stock 5.1.1 system**, which never comes up; USB never enumerates again (Windows last removal 14:15, nothing since, no ADB, no 0482:0a7f, no 05c6:9008). misc is cleared so it does not go to TWRP.

State to recover from (all data safe)
* `system` = stock 5.1.1 (verified). `boot` = Android 10 kernel #17 boot (unchanged). `recovery`, keystore, modem partitions, userdata untouched.
* Needed: get the phone into TWRP using the USB download-mode procedure in `KYF37-USB-RECOVERY-RUNBOOK.md` (battery out, SD with the three `DEVKEYDL` flag files - see SD folder `kyf37-download-triggers-disabled` if present - then the `request-kyf37-recovery-vendor.py` misc request, remove battery+SD, power on). Needs a human.
* Then, in TWRP, either `bash device-inspection/kycell-swap.sh stock` (write stock boot -> boots the real stock Android 5.1.1 = the baseline test; the system is already stock) or `bash device-inspection/kycell-swap.sh a10` (restore Android 10 system+boot from the SD copies; the script clears the proper temp-WP first and verifies by readback). Both finish with misc cleared and do not reboot.
* Baseline test to run on stock: `cat /sys/kernel/debug/smd/ch | grep -i -E "DATA5|CNTL"`, `ls /dev/smd*`, `dumpsys telephony.registry`; with and without a SIM. If stock shows DATA5_CNTL, diff the two systems' running services; if not, the cause is outside the software (SIM/perso/hardware/modem state).

## 10. Update 2026-10-09 (lead session): router service table, B20 persisted, QMUX probes
Measured on the running Android 10 phone (v17 + live fixes), after a fresh reboot:
- `/d/msm_ipc_router/dump_servers`: the modem node (0) publishes services 0x02 (DMS), 0x0e, 0x0f, 0x10 (LOC), 0x11, 0x12, 0x16, 0x17, 0x18, 0x1c, 0x1f, 0x21, 0x22, 0x24, 0x29, 0x2a, 0x2b, 0x2e, 0x2f, 0x30, 0x34, 0x35, 0x36. **NAS (3), UIM (0x0b), WMS (5), VOICE (9), WDS (1) are NOT published**: the modem has not started those tasks, so there is nothing to register with. `kyf37_qmi` (router lookup of NAS) reports `found=0`.
- `subsys_modem` state ONLINE, no crashes. SMD: `DATA5_CNTL` is OPENED on both APPS and MDMSW sides with traffic; `DATA1-4`/`DATA40` are OPENING on the modem side only.
- QMUX (`/dev/socket/qmux_radio`) client `device-inspection/kyf37_radio_ctl.c` (build: `_build_radio_ctl.sh`, clang-8 + bionic): NAS 0x34 (system selection preference) answers, but DMS 0x2d/0x2e (op mode get/set), NAS 0x24 (serving system) and UIM 0x2f (card status) time out (EAGAIN). The DMS set-mode (LPM then ONLINE) cycle gets no reply over QMUX either.
- **B20 / Spanish LTE mask is active and persistent**: NAS reads `0x0a0800c5` = B1,B3,B7,B8,B20,B26,B28 after reboot (written earlier with `kyf37_qmux --enable-spain`; the immediate read-back lagged, a later read showed it).
- Phone stays `OUT_OF_SERVICE` (voice and data), no operator. Not achieved: registration (LTE or 2G) and emergency-only service.
Open: why the modem never starts NAS/UIM/WMS/VOICE/WDS (candidates: Kyocera-specific handshake with the stock apps side, RF/NV state, SIM-lock gating). Needs the modem's own boot log (TWRP crash log) or a stock-Android baseline; stock flashing is off the table per the owner.
Diag probe (2026-10-09): `device-inspection/kyf37_diag.c` (build `_build_diag.sh`) switches /dev/diag to memory-device mode (ioctl 7, mode 2: ok) and sends the "enable all F3 message masks" command (`7d 05 00 00 ff ff ff ff`, raw with the 0x20 user-space type prefix: accepted), but only one 8 KB block with a mask-update header came back and no modem F3 text. Next steps if continued: register as a diag client the way diag_mdlog does (peripheral mask/real-time vote), then re-trigger the modem boot while capturing.
Diag probe result (2026-10-09, non-blocking rewrite of kyf37_diag): 31 KB captured in 25 s, but it is only the apps-side message-mask table (type 1, all zeros apart from range counts); no modem F3 packets (no 0x7e frames, no 0x79/qsr messages). So the modem is not streaming debug messages over /dev/diag in this configuration; getting them would need a full diag_mdlog-style session (peripheral registration, real-time vote) or the TWRP crash log.
