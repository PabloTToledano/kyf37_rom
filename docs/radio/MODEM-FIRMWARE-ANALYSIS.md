# Modem firmware analysis (host-only), 2026-10-10

Goal: find why the MPSS never publishes NAS(3)/UIM(0xb)/WMS(5)/VOICE(9)/WDS(1). **No root cause found.** This document records what was
established, what blocks further progress, and ranked hypotheses. Facts and guesses are separated. Nothing was run on the phone.

## 1. Method and tools (all reproducible)
| Step | Tool (in `modem-investigation/`) |
|---|---|
| Cut `modem` partition (p1, offset 1 MiB, 64 MiB, FAT16) out of `phone-backup/mmcblk0-corrected.img` | python slice |
| Extract FAT16 files without mounting | `fat16x.py image outdir` -> `fw/modem/IMAGE/*` |
| Reassemble `MODEM.MDT`+`MODEM.Bxx` into one ELF | `mbn2elf.py fw/modem/IMAGE MODEM fw/modem.elf` |
| Add section headers so objdump works | `wrapelf.py fw/modem.elf fw/modem.sec.elf` |
| Hexagon disassembler | **llvm-objdump 21** from Ubuntu `llvm-21`+`libllvm21` debs, unpacked with `dpkg -x` into `~/llvmdeb/root` (no root needed). The AOSP clang-r353983d has NO Hexagon target; capstone 5/6a11 has no Hexagon. `fw/dis.sh`, `fw/disall.sh` (writes `~/modemdis/segNN.txt`, ~7 M lines) |
| String/xref helpers (run in WSL) | `fw/xref.py` (string -> data refs -> code refs; msg_const struct = dataref-4), `fw/fn.py` (function listing with string annotation), `fw/dumpva.py`, `fw/findptr.py`, `fw/rcseq.py` (rcinit table decoder); wrappers `q.sh dv.sh fp.sh rs.sh fnr.sh` |
| Emulator available for later | `qemu-hexagon` (qemu-user 10.2 deb, downloaded to `~/qdeb`, not yet used) |

WSL note: the default shell is zsh; pass patterns via files (`q.sh patfile`) or `@` for alternation, never raw `|`.

## 2. Facts
1. ELF: e_machine 164 (QDSP6), **e_flags 0x5 = Hexagon V5**; 26 program headers; build string
   `MPSS.JO.1.0.c5.8-00133-M8909EAAAANVZM-1_20170729`. Disassembles sanely with `--mcpu=hexagonv5`.
2. **Part of the code is not readable offline.** Code for cm, mmgsdi/gsdi/uim, uimqmi, qmi_mmode (NAS/VOICE), qmi_wms/wms, pbm, ds/ps init,
   policyman, mmoc, reg, sd etc. has entry points at `0xd0xxxxxx`, a virtual range outside every program header. It lives in
   `MODEM.B21` (9.8 MB, ~7.84 bits/byte per page after the first 21 plain pages): the firmware contains `dlpager`, `dlpager_q6zip`
   tasks (`dlpager_q6zip.c`, `q6zip_partial.c`), i.e. **Q6ZIP demand-paged compressed code**. No public decompressor was found
   (web search negative). `MODEM.B20` is a plain zlib stream (2.78 MB, error/ULOG message tables, decodes fine: `fw/seg20_z0.bin`).
   Uncompressed seg12 (`0xc0729000`, 14.6 MB) holds rcinit, SMD/SMSM, EFS/RFS, DS core, RF, modem_cfg-adjacent code, the Kyocera log
   task and others, and was disassembled.
3. **rcinit table decoded** (`rcseq.py c1baa000 c1baa3a0`). Record layout: `{name, hash, type(7=task,2=init fn,1=policy), entry, prio, stack, affinity, ctx}`.
   Entries sit in blocks separated by NULL,NULL (group boundaries are my inference from that, not verified in rcinit code):
   - A (c1baa000): ulog_backend, time_*, modem_cfg(+_init), smd_test, ...
   - B (c1baa028): ftm_policy, mm_extern_init, mmgsdi_slot1/2_init, gsdi_init, mcpm, rf_*, slpc_*, ...
   - C (c1baa0c0): gsm/wcdma/tds/hdr, **mmgsdi_1/2, gsdi, uim_1/2, uimqmi(+_init), nvruim, simlock, policyman, modemkc_log(+_init)**, srch, ...
   - D (c1baa248): **qmi_modem, qmi_mmode, qmi_wms, qmi_pbm, wms, pbm, cm_init, mmoc, sd_init, reg, ds_init, ps_init, ims**, gps/loc, sm_*
   - E: secips, clm, secssl, dcvs;  F: rdm_opens.
   rcinit_init.c logs "initialization begins group", "function enter/exit", "group timer expire missing handshake" (strings at 0xc17fa4xx).
   Group timers are only used for termination; startup handshakes have no visible timeout string.
4. **Kyocera additions inside the modem** (strings, all `kc_*`): `bfss_cmd.c` (EFS backup to SMEM: "write to SMEM", `kc_smem_alloc error`),
   `nv_kc_init*` (NV initialisation groups 3gpp/3gpp2/bringout/dataset/devdrv/gps/omadm/rf/sysprop/efs, "[NV-INIT] initialize error!"),
   `mmgsdi_kc_lib.c` (SMEM_UICC_INFO get/set, slot1-only, filelog in EFS, IMSI/GID1 read), `simlock_kc_perso_policyfile.c`
   (policy file in EFS, `UIM_KC_NV_PERFECT_LOCK`, carrier VIRTUAL/OVERSEA), `uim_kc_lib.c` (virtual ICCID, `uim_check_rfs_gpio`,
   subsystem-restart state kill), `modemkc_log.c` (ring log in EFS `/modemkc/log`), `cmims_kc*.c`, `sd.c [KCDEBUG]`, `uimdiag_mmgsdi.c` kc test bits.
5. `modemkc_log_init` (readable, `0xc0a97258`) only does `efs_mkdir("/modemkc")`, `/modemkc/log`, logs failures and continues: it does not wait on the apps.
6. The rcinit record for `modemkc_log` is in group C, the same group as the whole UIM stack. UIM (0x0b) is missing while DMS (0x02) is present.
7. All of this agrees with `MODEM-STATUS-20261009.md`: SIM-in-slot test shows the modem is not waiting for a SIM; UIM is unpublished with or without one.

## 3. Unresolved inconsistency (important)
If rcinit starts groups in order and DMS comes from `qmi_modem` (group D), then group C (incl. `uimqmi`) must have completed its handshakes,
yet UIM is not published. Either (a) DMS is registered by something earlier (e.g. `qmi_fw`/`sys_m_qmi`/modem_cfg path, not `qmi_modem`),
(b) groups are not strictly sequential, or (c) UIM/NAS/WMS register later in their own task bodies after a wait that is itself blocked.
This cannot be settled without the Q6ZIP code or a live trace. Services present (0x0e,0x0f,0x10,...) were not mapped to tasks.

## 4. Ranked hypotheses (all UNPROVEN)
| # | Hypothesis | Evidence | Apps-side test |
|---|---|---|---|
| 1 | NV/EFS state: the modem's `nv_kc_init_func` / mcfg / mmgsdi / cm read EFS (`/nv/item_files/...`, `/mmgsdi`, policy file) through RFS; an `efs_*` call (or a Kyocera NV-init group, e.g. "efs", "rf", "sysprop") blocks or errors because the restored EFS is not what Kyocera init expects, or RFS (`rmt_storage`) answers late/wrong. | Most `kc_*` code is EFS-driven; stock apps use `rmt_storage` + `tftp_server` identically; EFS "pristine restore" was tried but only compared contents, not RFS timing. | From TWRP/Android: log `rmt_storage` requests (strace-less: `RMT_STORAGE` logcat tag, or kernel `rmt_storage` debug) and check that the modem opens `/dev/block/bootdevice/by-name/modemst1/2` + `fsg` with read AND write traffic; compare with a stock boot log (`radio-work/last_kmsg_boot*.txt`). |
| 2 | Bfss/SMEM handshake: Kyocera `bfss` exchanges EFS backup data with the apps over SMEM ("write to SMEM"/"read from SMEM", driver `OEM_bfss` / `/dev/OEM_bfss`); the modem may wait for the apps to read/ack. | `bfss_cmd.c` strings; apps kernel already has `OEM_bfss`. | Read what the modem wrote: dump SMEM item used by `kc_smem_alloc` (find item id in `0xc15c0bf8` neighbourhood / `bfss_backup_cmd_func` at ~`0xc09e4944`), via `/dev/smem_log`/`ramdump_smem` read-only. Only then consider writing. |
| 3 | A task in rcinit groups B/C/D blocks in its own init before `rcinit_handshake_startup`, stalling later work; likely candidates by being Kyocera-specific or apps-dependent: `mmgsdi_*`/`uim_*` (SMEM_UICC_INFO, `uim_check_rfs_gpio` waits on a GPIO via `DALSYS_BusyWait`), `modem_cfg`, `policyman`. | rcinit table; kc UIM code uses GPIO/RFS gating. | Needs decompressed d0 code, or a live modem task dump: DIAG "task list" (the `Task Name Pri Timeout... Is_Blocked` format string at 0xc17f92fd is the err/dog dump) - e.g. trigger a controlled `/sys/.../subsys` ramdump read-only after the hang and parse the task table. |
| 4 | MCFG/MBN: modem_cfg task needs an active `mcfg_sw.mbn` selected from `/mcfg` (EFS) or the 100+ MBNs in the modem partition (`image/modem_pr/mcfg/configs/...`); missing selection could hold dependent services. Seen: carrier is read as OVERSEA by apps. | `modem_cfg` task in group A; MBN tree present in firmware; `tftp_server` serves MBA/MBN. | Check `tftp_server` logs for `mcfg`/`modem_pr` file requests and whether any returned ENOENT. |
| 5 | SMSM handshake word: modem `0x08008009` lacks RUN(0x100) while apps has `0x1229`. | Only measured value; no stock reference. | Compare with `radio-work/` stock captures; low priority. |

Probably NOT it (evidence in older notes): SIM presence, kernel build, userspace daemons presence, firmware integrity.

## 5. What would resolve it (next steps for whoever continues)
1. **Decompress Q6ZIP**: reverse the `dlpager_q6zip` task (record at `0xc1810c14`, entry `0xc0c01d24`; uncompressed, in seg12) and run its own
   decompress routine under `qemu-hexagon` (deb already fetched) with a harness ELF; the page tables are likely in `MODEM.B19/B22/B23`.
   Output d0000000-based code makes `fn.py`/`xref.py` work for cm/mmgsdi/qmi_mmode. Largest-value item.
2. Map each present QMI service id to its registering task to resolve section 3.
3. Obtain a live modem task/blocked-state dump (hypothesis 3) - a phone-lock task, read-only.
4. Stock baseline log of modem boot (EFS/RFS traffic), if the owner ever allows one.

No safe write-test script was produced because no hypothesis is specific enough to justify writing to the phone's SMEM/EFS.

## 6. Confidence
- Extraction, ISA (V5), rcinit table decoding, Kyocera feature inventory: high.
- Group boundaries and the claim that groups gate each other: medium-low.
- Any root cause: **none established**; hypothesis 1 and 3 are the most plausible (low-medium).
