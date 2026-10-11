# Modem / cellular status — 2026-10-09 (end of session)

Goal given by the owner: make the KYF37 modem register on a network (emergency-only registration without a SIM, 2G included), and add the Spanish LTE bands, especially B20. No stock flashing (owner rule: only the custom Android 10 ROM).

## Result
- **B20 / Spanish LTE bands: done and persistent.** NAS system selection preference reads `0x0a0800c5` = B1, B3, B7, B8, B20, B26, B28 after reboots. It was written with `device-inspection/kyf37_qmux --enable-spain` (the immediate read-back lagged; a later read confirmed it). B38/B40 are not in the mask, and the modem's hardware band capability was never read, so support for each band is unverified.
- **Network registration: NOT achieved.** The phone stays `OUT_OF_SERVICE` for voice and data, with no operator name or network type, on LTE and on 2G. Emergency-only service is not achieved either.

## What was measured (running Android 10, v17 image + live patches)
- `subsys_modem` is ONLINE with zero crashes; the modem firmware is bit-identical to the original backup.
- SMD: `DATA5_CNTL` is OPENED on both APPS and modem sides with traffic. `DATA1-4` and `DATA40` are OPENING on the modem side only (nothing on the apps side opens them).
- IPC router server table (`/d/msm_ipc_router/dump_servers`): the modem node publishes services 0x02 (DMS), 0x0e, 0x0f, 0x10 (LOC), 0x11, 0x12, 0x16, 0x17, 0x18, 0x1c, 0x1f, 0x21, 0x22, 0x24, 0x29, 0x2a, 0x2b, 0x2e, 0x2f, 0x30, 0x34, 0x35, 0x36. **NAS (3), UIM (0x0b), WMS (5), VOICE (9) and WDS (1) are not published**: the modem never starts them, so there is nothing to register with.
- Over QMUX (`/dev/socket/qmux_radio`): only the NAS band-preference request (0x34/0x33) is answered. DMS get/set operating mode (0x2d/0x2e), NAS serving system (0x24) and UIM card status (0x2f) get no reply (EAGAIN after 10 s). A DMS LPM -> ONLINE cycle also gets no reply over QMUX.
- A fresh reboot changes nothing. `rmt_storage`, `tftp_server`, `qseecomd`, `time_daemon`, `qmuxd`, `netmgrd` and `rild` all run.
- `/dev/diag` probe: switching to memory-device mode and enabling all F3 message masks succeeds, but only the apps-side mask table came back (31 KB, almost all zeros). No modem debug messages were captured.

## Tools written (all in `device-inspection/`)
| File | Purpose |
|---|---|
| `kyf37_radio_ctl.c` (+ `_build_radio_ctl.sh`) | QMUX client: NAS band read/write, DMS operating-mode cycle (`--mode-cycle`), serving system and UIM probes. Built with the Android 10 tree's clang-8 against bionic (dynamic). Segfaults on exit, after the output is printed. |
| `kyf37_diag.c` (+ `_build_diag.sh`) | `/dev/diag` memory-device capture, non-blocking reads. |
| `kyf37_qmux`, `kyf37_qmi` (older) | NAS read/write over QMUX; router lookup of NAS. |

Build tip: the Android tree's gcc/clang wrappers need `/usr/bin/python`, which WSL lacks; call `clang-8` directly from `prebuilts/clang/host/linux-x86/clang-r339409b/bin`, with stub `linux/compiler*.h` headers (see `_build_radio_ctl.sh`). Put WSL commands in script files; inline `bash -c` with variables expanded to empty.

## Ruled out
Kernel build, Android 10 userspace, qseecomd/TrustZone listeners, EFS contents (pristine restored), modem firmware, dpmd/ssr_setup, the stock kernel with stock daemons in TWRP, a phone reboot, DMS mode cycle, enabling all F3 masks, the band mask itself.

## Open and what would unblock it
Why does the modem never start NAS/UIM/WMS/VOICE/WDS? Leading hypotheses: a Kyocera-specific handshake with the stock apps side (shared memory), RF/NV state, or SIM-lock gating.
1. Read the modem's own startup log from TWRP (`/proc/last_kmsg`, crash logs), or finish a `diag_mdlog`-style client (peripheral registration, real-time vote).
2. Test with a SIM in the slot (physical).
3. Stock Android 5.1 comparison (owner has ruled out flashing the original ROM).

## Incident to remember
During a stock-baseline attempt a previous agent wrote the stock system without the stock boot, which left the phone unbootable until the USB download-mode recovery was done by hand. Boot writes need `clear-recovery-boot-temp-wp` first. Recovery procedure: `KYF37-USB-RECOVERY-RUNBOOK.md`. The phone now runs the v17 image; `public.libraries-kyocera.txt` was removed live to fix a zygote abort (source fix: `fix-android10-remove-kyocera-public-libs.py`).

See also: `RADIO.md` sections 8-10.

## Update 2026-10-10: SIM-in-slot test (owner inserted a SIM, PIN-protected)
Measured on v19 (uptime ~4 min after a boot with the SIM in): the modem node still publishes only services 0x02, 0x0e, 0x0f, 0x21, 0x22, 0x24, 0x29, 0x2a, 0x2b, 0x2e, 0x2f. UIM (0x0b) and NAS (3) are still NOT published, so the modem is **not** waiting for a SIM. Android side: rild/qmuxd/netmgrd run, but UiccController logs `RADIO_NOT_AVAILABLE` for slot/card status and `gsm.sim.state` is empty, so Android never learns that a card exists and no PIN screen appears. `ril.radio.kc_area_info=OVERSEA`, `ril.subscription.types=NV,RUIM`, baseband `909EAAAANVZM-1.169552.1.179667.2`. Conclusion: hypothesis "modem waits for a SIM" is refuted; the missing-services problem is independent of the SIM. Do not enter the PIN anywhere until the card shows up in `dumpsys telephony`/`getprop gsm.sim.state` (wrong attempts lock the SIM).

## Update 2026-10-10 (lead): more things ruled out, none changed the result
- **Holding /dev/subsys_modem open** (nothing on v19 holds it; stock pm-service/libperipheral_client would): router service list unchanged at +5/15/30/60 s, SMSM unchanged (apps `0x00001229`, modem `0x08008009`), subsys ONLINE. Not the cause.
- **kcpdsm** (`security/misc/kcpdsm.c`) is only a sysfs process-list helper for lkspad, nothing to do with the modem. **uimd** is a Kyocera NFC/FeliCa helper that is a *client* of the modem UIM service (downstream, not a cause). `init.kdmc.rc` services are factory `*_diag` tools.
- Kyocera nodes exist: `/dev/OEM_bfss`, `/dev/dnand_cdev`, `/dev/kclog_smem`, `/dev/ramdump_smem`, `/dev/smem_log`; partitions `dnand`, `modemst1/2`, `fsg`, `sec`, `ssd`, `persist` are present. Carved EFS images contain no readable text.
- Modem state words do not decode to a "RUN" state with the standard bits in `include/soc/qcom/smsm.h` (modem `0x08008009` has unnamed bits `0x8000`, `0x08000000`); no stock-era value is on record to compare against.
- Unchanged: DMS answers on the IPC router, but NAS/UIM/WMS/VOICE/WDS are never published, with or without a SIM.
Remaining hypotheses (unproven): modem-side Kyocera SIM-lock/perso layer (`mmgsdi_kc_lib`, `UIM_KC_NV_PERFECT_LOCK`, `SMEM_UICC_INFO`) waiting on an apps-side contribution; missing MCFG/MBN config; boot-mode word (`androidboot.mode=kcpermissive`). Each needs the modem's own log or a stock reference.

## Update 2026-10-10 (firmware RE agent) - see MODEM-FIRMWARE-ANALYSIS.md
Modem image is Hexagon V5 (MPSS.JO.1.0.c5.8, M8909EAAAANVZM), disassembled with an unpacked llvm-21 hexagon objdump (~/modemdis). rcinit boot-task table decoded: qmi_mmode (NAS/VOICE) and qmi_wms start in the LAST block with cm/ds/qmi_modem; the whole SIM/UIM stack and the Kyocera log task are in the block before. Kyocera additions (bfss, nv_kc_init, mmgsdi_kc_lib, SIM-lock policy file, modemkc_log) are EFS/SMEM driven; modemkc_log_init only creates EFS dirs (no apps wait). NOT found: why the later block never runs - cm/mmgsdi/uim/mmode/wms/ds code is Q6ZIP-compressed in MODEM.B21 (no public decompressor; idea: run the firmware's own pager under qemu-hexagon). Lead-side check: in the stock system only the factory tool `bfss_diag` touches /dev/OEM_bfss (no daemon), so the bfss hypothesis is not a missing Android userspace piece.

## Update 2026-10-10 (modem-logs): see MODEM-LOGS-20261010.md
A working /dev/diag client (device-inspection/kyf37_diag2.c, HDLC-framed commands) captured the modem F3 log: the modem is fully booted (mmgsdi/uim/cm/mmoc/reg/wms/ims run, SIM ATR read, PIN1 event, ONLINE_GWL, GSM camped), so "the modem never starts NAS/UIM" is refuted; DMS 0x2d / NAS 0x24 / UIM 0x2f requests are accepted at CTL level but never answered. EFS (modemst1/2) is encrypted. The diag driver has heap-corruption bugs: never send 0x7d 0x05.

## Update 2026-10-11 (lead): THE MODEM WORKS; the fault is in the Android radio layer (supersedes earlier "modem never starts services")
Evidence (all measured on v19, kernel #17):
- **My earlier probe tool was malformed** (QMI message id passed as the QMUX msg type, empty body), so every DMS/NAS-serving/UIM "no reply" result was an artefact. Fixed in `device-inspection/kyf37_radio_ctl.c` (`svc_roundtrip` now builds `[flags][txn][msgid][len][TLVs]`). With valid frames over qmuxd/QMUX (/dev/smdcntl0): DMS get op mode (0x2d) -> **ONLINE (0)**; NAS get serving system (0x24) -> state 2 "not registered, searching", GSM, **PLMN MCC 214 MNC 03 (Orange ES) visible**, signal weak (RIL cell info: GSM LAC 33040 CID 1497 rssi -113); UIM get card status (0x2f) -> card present, USIM, PIN1 required (modem log: `MMGSDI_PIN1_EVT status 1`, ATR read, `Unknown SIM ... In japan area:1` Kyocera logic).
- Modem F3 log (MODEM-LOGS-20261010.md): UIM/MMGSDI/CM/MMOC/QMI mmode/WMS/WDS tasks all run, MMOC goes ONLINE_GWL, GSM L1 CAMPED. The IPC-router service list is irrelevant: services are reached via QMUX/SMD.
- **Android side:** qcril (libril-qc-qmi-1, RIL version 11 from Android 5.1) talks QMI fine (card status UNKNOWN->UP, signal strength, emergency-number indications registered). But after `RADIO_POWER on`, RILJ gets `UNSOL radioStateChanged: 1` (RADIO_STATE_UNAVAILABLE) and UiccController logs `RADIO_NOT_AVAILABLE` / `RIL_REQUEST_GET_ICC_STATUS ... INVALID_RESPONSE`. rild logs `RILC: getIccCardStatusResponse: Invalid response` (Android 10 hardware/ril/libril/ril_service.cpp:3030 rejects responses with len != sizeof(RIL_CardStatus_v6)=280, NULL, or app index >= num_applications) and `RILC: responseInt: Invalid response`; `RIL_REQUEST_START_LCE` also INVALID_RESPONSE. In one run qcril logged `qcril_send_request_response ... GET_SIM_STATUS Success, Len 284` (284 != 280). Because Android never gets a SIM status it has no SIM state, no PIN screen (card needs PIN 1632 from the owner; do NOT type it blindly), no registration.
- Experiments this session: patched libril (`device-inspection/fix-android10-ril-cardstatus.py`, KYF37_RIL_MODE=diag|accept; accepts len >= 280 and logs a hex dump) built (`m libril`, 54 s) and installed live at /system/vendor/lib/libril.so (original: radio-work/ril-patch/libril.orig.so md5 438629c1..., also /data/local/tmp/libril.orig.so on the phone). After a full reboot with the "accept" build, Android still gets INVALID_RESPONSE at boot (20:25:08 in the phone's reset clock) and the diag line did not print, i.e. at that moment the response is NULL, not 284 bytes: the first GET_ICC_STATUS arrives before qcril has the card status, and nothing re-requests it afterwards because qcril keeps the radio in RADIO_STATE_UNAVAILABLE.
- Still unknown (next work): why qcril reports RADIO_STATE_UNAVAILABLE after power-on (qcril 'android service state' / init of all QMI clients: qmux reports `QMI_PORT_NOT_OPEN (-5)` for conn_ids 29/48/57 about 170 times (netmgrd/qcril data ports), only conn 0 /dev/smdcntl0 is open), and whether the 284-byte struct (extra 4 bytes) is later accepted/misparsed. Tools: qcril debug logging with `setprop persist.radio.adb_log_on 1` (floods; enlarge log with `logcat -G 16M`).

## Update 2026-10-11 (radio-sim): SOLVED SIM status -> see MODEM-RIL-FIX-20261011.md
Radio state was never stuck at UNAVAILABLE (RILJ logs TelephonyManager values 1=ON, 2=UNAVAILABLE). Real cause: qcril's 284-byte card status has a 7-word header; Android 10 libril rejected it. Converter added (`fix-android10-ril-cardstatus.py`). Verified live + after reboot: `gsm.sim.state=PIN_REQUIRED`, subscription listed, `mIsEmergencyOnly=true`, SIM PIN screen shown (no PIN entered). Registration after PIN is unverified.

## Update 2026-10-11 (lead): registered; band capability measured
- After the owner entered the SIM PIN the phone is registered: voice+data IN_SERVICE, modem NAS state 1 (registered, CS+PS attached, GSM, Spanish PLMN). Real GSM strength about -67..-69 dBm.
- **Hardware LTE band capability (DMS 0x45 TLV 0x10): 0x0000000002000001 = B1 and B26 only.** (TLV 0x01 2G/3G/other mask 0x04680380; TLV 0x11 = 0.) The LTE *preference* mask is 0x0a0800c5 (B1,B3,B7,B8,B20,B26,B28) and is accepted/stored, but the modem can only use bands the RF hardware/config supports, so on LTE this phone can only camp on B1 (2100 MHz; used by all three Spanish operators) and B26 (Japanese 850, not used in Spain). B3/B7/B8/B20/B28 (and B32/B38/B40) cannot be made to work by software if the capability is real hardware. Not verified: whether capability is limited by RF NV rather than hardware (not testable without the RF NV tools); GSM 900/1800 and WCDMA work (cells seen at ARFCN 31 etc.).
- Tool: `kyf37_radio_ctl` now prints DMS band capability and supports `--set-lte <hex mask>` (also `--enable-spain`).
- Movistar APNs present in /system/etc/apns-conf.xml: MCC 214 MNC 07 'Movistar' telefonica.es (default,mms,supl, mmsc http://mms.movistar.com, proxy 10.138.255.5:8080), 'Movistar ES Internet' movistar.es/MOVISTAR, 'Conexion Compartida' (dun), 'Movistar ES IMS' ims; also MNC 02 entries. Orange 214-03, Vodafone 214-01/06, Yoigo 214-04, DIGI 214-22 etc. are present too.
- Signal bars flicker: the modem is stable but Android's GSM rssi alternates -67/-69 and 2147483647 (unknown); handed to an agent (MODEM-SIGNAL-DATA-20261011.md).

## Signal flapping + mobile data fixed - 2026-10-11
rild crash loop (qcril setup_data_call reads data[8], libril sent 7 strings) caused the service-state/signal flapping and blocked data. Fix `fix-android10-ril-setupdata.py`; live libril installed; data CONNECTED on rmnet_data0 and ping OK. See MODEM-SIGNAL-DATA-20261011.md.
