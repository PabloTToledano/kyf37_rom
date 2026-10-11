# Modem-side evidence, 2026-10-10 (modem-logs agent)

Short version: **the modem is not stuck in boot.** A working /dev/diag client now delivers the modem's F3 log. It shows the mmgsdi/uim/cm/mmoc/sd/reg/wms/ims/qmi tasks running, the SIM detected (ATR read, PIN1 event), MMOC reaching ONLINE_GWL and GSM L1 camping. The EFS partitions cannot be read (encrypted). The real gap is between the apps side and the services: DMS/NAS-serving/UIM requests over QMUX are never answered, although CTL `get_client_id` for those services succeeds.

## 1. Captured files (all under `radio-work/efs-20261010/`)
Read-only `dd` copies from the running phone (nothing was written to any partition):

| file | size | sha256 (first 16) |
|---|---|---|
| modemst1.bin | 2 MiB | 0de078fe2de909e0 |
| modemst2.bin | 2 MiB | eb7aeec7e0396db6 |
| fsg.bin | 2 MiB | 5647f05ec1895894 (all zero) |
| fsc.bin, sec.bin, ssd.bin | 512 KiB | 07854d2fef297a06 (all zero) |
| dnand.bin | 8 MiB | bf712b919b607159 |
| fw/modem.b* | pulled from /firmware/image for string/hash lookup | |
| diag2_boot.txt / .raw | F3 capture from 14 s after apps boot, 75 s, 57 883 packets | txt e5f46469, raw 7c615435 |
| diag2_exp1.txt / .raw | capture while `kyf37_radio_ctl` probes DMS/NAS/UIM | txt 653ca3ae |
| decoded_boot_arrival.txt, decoded_boot_79_chrono.txt, decoded_boot_summary.txt, decoded_exp1_arrival.txt | decoded output (arrival order) | |
| last_kmsg_diag2_crash.txt, last_kmsg_diag2_crash2.txt | panics caused by the diag driver bugs (section 4) | |

## 2. EFS (route 1): result
- `modemst1/2`: sector 0 is a plain header (`IMGEFS1`/`IMGEFS2` plus a write counter: 0x1a1e / 0x1a1d now; earlier dumps 0x184e, 0x19a4, 0x19d4, so the modem keeps writing its EFS). Sectors 1..1791 (896 KiB) have entropy 7.95-7.96 per 4 KiB, no repeated 16-byte blocks, no zlib stream, and every sector differs between any two dumps (new IV per write). They are encrypted or randomised by the modem: no path strings, no EFS2 superblock. **I could not extract the file tree.** rmt_storage only moves sectors (no crypto in it).
- `fsg` (golden copy), `fsc`, `sec`, `ssd`: all zero. `dnand` (Kyocera "DNAND"): stock-era kclog (2019 `RestartReason=` records, `Intent Log (SIM(CARD_IO_ERR))` x24 from the stock days, battery logs). Our ROM does not touch it (10 header bytes differ between Oct 9 and Oct 10).
- So the EFS-content hypotheses (FTM flag NV 453, perso, policy files) cannot be tested offline; the F3 log is the substitute.

## 3. Diag client (route 2)
Source `device-inspection/kyf37_diag2.c`, build `device-inspection/_build_diag2.sh` (clang-8 from the tree), helper `device-inspection/_exp1.sh`, decoder `radio-work/efs-20261010/analysis-scripts/decode_f3.py`. Run as root (`adb root`): `kyf37_diag2 <secs> -` (text to stdout, raw to /data/local/tmp/diag2.raw). It leaves the driver in USB mode when done.

Why `kyf37_diag.c` saw nothing: `diagchar_write(USER_SPACE_DATA_TYPE)` runs `diag_process_hdlc()`, so commands must be **HDLC framed with CRC-16**; raw commands were silently dropped ("bad CRC"). With framing, the modem answers version (0x00), 0x1c, 0x7c ext build id (`MPSS.JO.1.0.c5.8-00133-M8909EAAAANVZM-1.169552.1.179667.2`, build May 30 2019), 0x1d and the ssid-range query (25 ranges). Setting each msg-mask range exactly as reported makes the modem stream F3: ~58 k packets in 75 s. Packet types: 0x92 (QSR4 hashed terse, 88 %), 0x79 (format string embedded, readable), few 0x10/0x60. Read format: `[0x20][num]{[len][HDLC data]}*`.
Hashed messages: the 32-bit hash appears in `modem.b14` inside a table of `{u16 file-id, u16 line, u32 hash}` records, so hash -> (file-id, line) is recoverable, but the file-id -> name map and the format strings are not on the device. Not completed.

## 4. Kernel bugs found in this 3.10 diag driver (cost two phone reboots; do not repeat)
1. `diag_cmd_set_all_msg_mask` (0x7d 0x05, non-zero mask) -> `diag_send_msg_mask_update()` never resets `mask_size` inside its loop for the ALL_ENABLED case, so the control packet grows x4 per range and overflows the 4 KB `update_buf`: heap corruption, panic in an unrelated driver (`msm_bus_dbg_client_data` in `devfreq_monitor`). Reproduced twice (see `last_kmsg_diag2_crash*.txt`).
2. The msg/event/log mask update functions `krealloc()` the buffer but keep writing through the stale local pointer (use-after-free whenever a range needs a bigger buffer). Avoided by setting every range exactly as reported.
The client only sends exact-range sets plus the event toggle; the arguments `allmask` / `unsafe` reproduce the crash paths. Never use them.

## 5. Decoded timeline (modem F3, boot capture)
Time = ts/65536*1.25 ms; the absolute value is not uptime (the counter survives apps reboots). The capture starts ~14 s after apps boot, so early rcinit steps are not covered (rcinit writes no text for them anyway).

| modem t (s) | event |
|---|---|
| 8473.9 | UIM_1 reads the ATR (3B 9F 96 80 1F C7 80 31 E0 73 FE 21 1B 64 41 91 71 ...: a USIM); `efs_read terminal_profile size:31`; MMOC `Trans_state 14 WAIT_SESSION_OPEN_CNF`; CM `uim_carrier_type(0) is_sms_mandatory(1)` |
| 8474.0 | `MMGSDI_SESSION_OPEN_CNF` (valid session), `MMGSDI_SESSION_CHANGED_EVT`, `MMGSDI_PIN1_EVT status 1 slot 1` |
| 8474.7 | `qmi_uim_tlv_event_reg mask 0x805` (a UIM client registered) |
| 8485.0 | `qmi_ctli_get_version` handled (QMI CTL alive on DATA5_CNTL) |
| 8486.6 | MMOC `OPRT_MODE_CHGD` -> PWR_DOWN -> LPM; CM: `Unknown SIM is detected`, `In full/limited service:0, In japan area:1, Is target SIM:-1` (Kyocera cm.c / sd.c [KCDEBUG]) |
| 8490.1 | CTL get_client_id, `qmi_wdsi_bind_mux_data_port` (WDS is served) |
| 8493.6 | MMOC `OPRT_MODE_CHGD` -> `New transaction 2(ONLINE)`, `Prot_state [MAIN] 5(ONLINE_GWL)` |
| 8496.6 on | GSM L1/RR `IMMEDIATE_ASSIGNMENT / PAGING_REQUEST / MEAS_IND state CAMPED` repeating; WLAN FW traffic; IMS tasks; A2/MCPM power logs |

No assert, fatal, timeout or EFS error text. The only error-like lines: `Error opening file /nv/item_files/modem/data/3gpp/lteps/profile_list` (optional file), `RR_INVALIDATE_SIM_DATA_REQ in RR_INACTIVE`, `qpDplStorePLANIDataInNV DCM_ERROR_UNKNOWN`. Apps-side lines (ssid 65, qmuxd/netmgrd): `qmi sys error code -5` (QMI_PORT_NOT_OPEN) 170 times for conn_id 29/48/57; only conn 0 (`/dev/smdcntl0`, the single SMD port qmuxd holds open) works, and UIM indications (`srvc=11`, msg 0x32) arrive on it.

Experiment (diag2_exp1): CTL `get_client_id` for DMS(2), NAS(3) and UIM(11) is handled and succeeds; the following DMS 0x2d, NAS 0x24 and UIM 0x2f requests produce no dispatch log and no reply (EAGAIN after 10 s). The NAS band-pref request (0x34) is dispatched (svc 3) and answered.

## 6. Cross-reference with MODEM-FIRMWARE-ANALYSIS.md (rcinit blocks)
Block A (modem_cfg, time), B (mmgsdi_init, mcpm, rf), C (gsm/wcdma, **mmgsdi_1, uim_1, uimqmi, nvruim, simlock, policyman, modemkc_log**) and D (**qmi_modem, qmi_mmode, qmi_wms, wms, pbm, cm, mmoc, sd, reg, ds, ims**) all demonstrably run (they log). **The modem is not stuck in any rcinit block**; it has passed D (E/F not checked). This settles the "unresolved inconsistency" of that document: the services exist and run, but they are not usable the way the apps side expects (not on the IPC router; some QMUX requests unanswered). Its hypotheses 1 (EFS/NV init blocking), 3 (a task blocked before handshake) and 4 (MCFG) are not supported by this log.

## 7. Ranked causes (facts vs guesses)
1. **Fact, confidence 90 %**: the modem is fully up and its QMI services (UIM, WDS, NAS band, CTL, CM-side qmi_mmode) run. "The modem never starts NAS/UIM/WMS/WDS" is refuted. The SIM is detected (not waiting for it).
2. **Guess, 55 %**: transport mismatch. The services answer on QMUX/SMD DATA5_CNTL (30 services in the CTL version list) but are not on the IPC router that QCCI users see. Whether the patched `libril-qc-qmi-1` uses QCCI-over-IPCR or qmuxd is not yet known.
3. **Guess, 45 %**: requests that need CM/MMGSDI (DMS op mode, NAS serving system, UIM card status) are accepted at CTL level but never answered; a handler blocked on a CM/MMGSDI command (Kyocera "Unknown SIM" / Japan-area logic, concurrent LPM->ONLINE cycle). No handler log appears for them.
4. **Guess, 30 %**: Kyocera carrier logic (`ril.radio.kc_area_info=OVERSEA`, SIMLOCK_KC_CARRIER_OVERSEA, `is_japan=1`, "Is target SIM -1", "Not allowed to access Japan PLMN") keeps service at none/limited. Explains missing registration, not missing services.
5. Ruled out / low: crash or watchdog (none), EFS corruption (EFS keeps being written, no EFS errors), SIM wait, subsystem restart, rcinit stall, diag itself.

## 8. Concrete next test
Reboot, run `kyf37_diag2` immediately and in parallel record what rild and qmuxd open (`ls -l /proc/$(pidof rild)/fd`, `logcat -b radio`) to learn whether qcril uses the IPC router or qmuxd. Then repeat the DMS 0x2d probe while capturing; if the modem still shows no `qmi_svc` dispatch, enable qmuxd/libqmi debug (`persist.radio.adb_log_on`) to check whether the frame is written to `/dev/smdcntl0`. Optionally map the ssid 5000 hashes to file/line through the `modem.b14` table. Use only exact-range msg-mask sets.
