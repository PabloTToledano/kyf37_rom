# USB recovery and stock restore (KYF37)

Moved verbatim from KYF37-PROJECT.md on 2026-10-11. Historical incident dates are evidence; the runbook itself is current.

## Verified USB recovery procedure (historical incident, still applicable)

Successfully restored 2026-10-07. This is a recovery runbook for this specific phone and its local backups. Read the outcome section before acting. It supersedes earlier claims that a Firehose programmer is required or that this download mode cannot access storage.

## Device and incident

- Kyocera GRATINA KYF37, MSM8909, eMMC, Android 5.1.1 stock.
- Android/ADB serial: `981108631314`. Sahara serial: `0x126a2083`.
- A custom Android 7.1.2 ROM caused repeated GRATINA splash restarts. Physical key combinations did not reach recovery.
- Installed recovery: owner-signed TWRP `3.7.0_9-0`. The matching owner signing keystore must remain paired with owner-signed boot/recovery images.
- Use the backups and tools on this computer. The user explicitly rejected using another computer's files and required USB/software-only recovery.

## Confirmed outcome so far

1. Entered the phone's custom Sahara download mode using microSD flags.
2. Demonstrated vendor eMMC reads and writes without uploading any programmer.
3. Read and validated live GPT, recovery, keystore, boot, and misc.
4. Wrote a recovery request into misc, verified exact storage readback, removed the microSD, and restarted. **The user confirmed recovery worked; ADB independently identified KYF37 TWRP with root access.**
5. Restored stock system and the owner-signed pre-ROM stock boot. Both written partitions passed SHA-256 readback checks. Recovery and keystore also passed unchanged hash checks.
6. Removed only the temporary restore staging files from `/data/local/tmp/kyf37-stock-restore`, freeing about 2 GB. Userdata was not wiped or restored.
7. Rebooted. ADB briefly reported Android **5.1.1**, then disconnected before `sys.boot_completed=1` was observed. **The user subsequently confirmed the normal home screen. Stock startup is therefore confirmed by the user, with independently verified system/boot readback and Android version.** ADB boot-completed was not independently observed. The phone was restored successfully.

## Working recovery entry

### Prepare download mode

With battery removed, place a FAT32 microSD in the phone with these root files. Each contains exactly eight ASCII bytes `DEVKEYDL`, without newline:

```text
NOTPUSH
CHKCODE
FASTBOOT
```

`NOTPUSH` and `CHKCODE` are confirmed in stock SBL1. `FASTBOOT` was present in the working original card configuration; its filename is not a proven fastboot trigger. Do not leave `SDDLFLAG`, `set.bin`, or `REC_MISC.BIN` active at the card root. Previous SDDL attempts did not obtain recovery.

Insert battery, power on, connect USB. Expected VID:PID is **0482:0a7f**, not necessarily Qualcomm 05c6:9008. A screen or LED is not proof of the protocol: check USB and handshake.

If Linux access is denied, inspect `device-inspection/enable-kyf37-usb.sh`. A user-run sudo command previously installed a temporary rule under `/run/udev/rules.d/99-kyf37-recovery.rules`, granting pablo access only to 0482:0a7f. The rule disappears at computer reboot. Do not assume sudo is available to the agent.

### Use the vendor protocol, not Firehose

Python environment: `device-inspection/recovery-venv/bin/python` (PyUSB/libusb).
Endpoint OUT `0x01`, IN `0x81`. Integers are **little-endian uint32**.

1. Send switch-mode packet `(0x0c, 12, 3)` to request a fresh hello.
2. Require a 48-byte hello, command 1, protocol version 2.
3. Send hello response `(2,48,2,1,0,3,0,0,0,0,0,0)`.
4. Require command-ready `(0x0b,8)`.
5. Vendor **read**: `(0xa3,16,start_lba,byte_count)`. Response `(0xa4,16+byte_count,start_lba,byte_count)` followed by data.
6. Vendor **write**: `(0xa1,16+byte_count,start_lba,byte_count)` followed by data in the same packet. Response `(0xa2,16,start_lba,byte_count)`.

For this implementation, keep payloads sector-aligned and **at most 0x3e00 bytes**. Sector size is 512. Always validate response headers/lengths and read back every write. Do not send writes while investigating read compatibility.

Static evidence from the exact backed-up SBL1:

- Vendor dispatch `0x08017290`, separate from standard command-mode EXE_REQ callback.
- A3 read handler `0x0801674c` calls eMMC read `0x0801bbd0`.
- A1 write handler `0x080167d0` calls eMMC write `0x0801bc18`.
- These handlers require state `0x0b`, established by the command-mode handshake above.
- Standard Sahara EXE_REQ supports only serial command 1 on this device. Its rejection of HWID/hash/streaming commands does **not** imply vendor storage commands are absent.

Working local tools, in this order:

```bash
device-inspection/recovery-venv/bin/python device-inspection/probe-kyf37-vendor-read.py
device-inspection/recovery-venv/bin/python device-inspection/read-kyf37-live-partitions.py
device-inspection/recovery-venv/bin/python device-inspection/request-kyf37-recovery-vendor.py
```

Read the scripts first. The first establishes command mode and reads LBA0. The second requires that state, validates both primary GPT CRCs and every backed-up partition geometry, and captures live images. The third rechecks recovery/keystore and writes only the three misc sectors. It refuses if live misc differs from the fresh snapshot. Keep fresh copies of current diagnostic files before rerunning because these scripts use fixed output names.

Shared read transport: `device-inspection/kyf37-vendor-usb.py`.

### Recovery request details

On this verified GPT, `misc` starts at **LBA 15022080**. The request occupies Android's first 1088-byte bootloader-message structure:

- command[32], byte 0: `boot-recovery` plus NUL padding;
- status[32], byte 32: zero;
- recovery[1024], byte 64: `recovery\n` plus NUL padding;
- **no wipe arguments**.

Read three sectors (1536 bytes) first, save them, modify only the first 1088 bytes, and preserve bytes 1088–1535. Send A1, require A2, then A3-read and compare every byte. Existing script does these checks. Do not write GPT, SBL, aboot, keys, or the full disk just to enter recovery.

After successful readback: **remove battery, remove microSD, reinsert battery, power on connected to USB.** The SD trigger otherwise forces download mode again. The installed TWRP then booted successfully in this incident. TWRP/aboot consumed and cleared misc; its first three sectors were zero before the eventual stock reboot.

## Restore stock from TWRP

Require `adb devices -l` to show serial `981108631314` in `recovery` state, model KYF37. Independently verify root, model, serial, TWRP version, partition symlinks/sizes and source hashes. Use `adb -s 981108631314` for every command.

Working restore script: **`device-inspection/restore-stock-kyf37.sh`**. Read it before running. It verifies staging files, live recovery/keystore, checks system is unmounted, clears only temporary eMMC write protection, writes system then stock boot, and verifies full block readback. On failure remain in TWRP. It does not reboot automatically.

Staging directory on phone: `/data/local/tmp/kyf37-stock-restore`.
Stage the stock system as `system-stock.img`, pre-ROM boot as `boot.img`, both temporary-write-protection helpers, and the restore script. Ensure sufficient free space. In this incident a gzip level-1 copy reduced USB transfer from 1.6 GB to about 528 MB, then was decompressed into the staging directory with `/sbin/busybox gunzip -c`. Hash the decompressed full image before writing.

Invoke:

```bash
adb -s 981108631314 shell '/sbin/sh /data/local/tmp/kyf37-stock-restore/restore-stock-kyf37.sh > /tmp/kyf37-stock-restore.log 2>&1; result=$?; tail -20 /tmp/kyf37-stock-restore.log; exit "$result"'
```

Only success with **`KYF37_STOCK_BOOT_SYSTEM_READBACK_VERIFIED`** confirms all script checks passed. Pull the log before reboot. Remove only the known files created in the staging directory after verification; do not delete other `/data/local/tmp` contents. Leave the microSD removed, then `adb -s 981108631314 reboot`.

The bundled BusyBox **does not support `stat -c`**. Use `stat -t` and its second field for file size. The working script has been corrected accordingly. SHA-256 of the full system on this phone takes roughly a minute; the system write took 56 seconds. Do not interrupt power during writes or mistake a quiet hash step for a hang.

## Authoritative backup hashes

| Image | Local path | Bytes | SHA-256 |
|---|---|---:|---|
| Stock system | `device-inspection/system-stock.img` | 1612709888 | `76bbf8b49dffd8118f6c7cb8e15559aa1fee2e167a7ce31728239201c14c6f01` |
| Owner-signed stock boot | `phone-backup/pre-rom-20261007/boot.img` | 16777216 | `466fd5ead33dabb54446ecf2f2132edc821e8d7da0c2f5d9f61fb08c45bcc3ed` |
| Installed TWRP | `phone-backup/pre-rom-20261007/recovery.img` | 16777216 | `9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e` |
| Installed owner keystore | `phone-backup/pre-rom-20261007/keystore.img` | 524288 | `0a689db00c0fc8029748f431760965b67da4f1d345d3dd5508c5f3362ce3bf4c` |
| Full original disk | `phone-backup/mmcblk0-corrected.img` | 7818182656 | `22005a4d3bd70cff24f59c9e5bdf1c5a63fd7c37607390d5676e4517c05168fc` |

Geometry: `phone-backup/partition-map.json`; source metadata mentions Windows, but the image bytes used here are verified local backups. Boot is mmcblk0p10, system p15. Verify live GPT; never infer geometry from another Kyocera model.

Helpers:

- `clear-system-temp-wp`: SHA-256 `958575ecb6b1a4a8f6d909f22a7412adfef03861bad1782b2b3baccd7bb5b9c9`; source `device-inspection/clear_system_temp_wp.c`.
- `clear-recovery-boot-temp-wp`: SHA-256 `faf20446c1196ae8289344eb1585450c9f18e3a34e3491bd5f150751843ab550`; source `device-inspection/clear_recovery_boot_temp_wp.c`.
- Both guard exact eMMC geometry and refuse permanent/power-on protection. They issue CMD29 only for temporary protection, then verify.

Pre-ROM TWRP boot/system/data archives are also safely on host under `phone-backup/microsd/kyf37-pre-lineage-20261007`. Their recorded MD5 digests were verified. Data archive excludes internal media. Do not restore/wipe userdata unless required by diagnosed startup failure and authorized scope; this successful partition restore preserved it.

## What failed and what not to assume

- Two generic MSM8909 Firehose uploads disconnected before successful execution. No Firehose write was performed. Do not repeat arbitrary programmer uploads when vendor A3/A1 already works.
- An offline audit of 80 applicable public programmers found no SBL root-key match. This is no longer a blocker for this custom vendor protocol.
- SDDLFLAG experiments, including a decoder-validated minimal misc package, caused continued bootloops. All active package files were removed from card root. The later live read showed misc all zero before the direct vendor write.
- Certificate labels, different SBL/aboot root keys, or Boot Config `0xe1` do not prove the secure-boot fuse state. Do not claim secure boot is disabled.
- Do not flash original OEM boot alone while the owner keystore is installed. Use the verified owner-signed pre-ROM stock boot above.
- Do not flash E4610/E4810 firmware or run their aboot flasher on KYF37. Their research suggested the protocol, but actual KYF37 handlers and live reads/writes were independently verified here.
- Do not use USB device reset routinely: a prior reset hung the host kernel. Switch-mode can request a fresh handshake.
- Memory-debug reads whose sizes are multiples of 512 require draining a USB zero-length IN packet; forgetting it causes transport stalls. Vendor A3 responses have a 16-byte header and use the separately validated transport.

## Evidence and further diagnosis

- `device-inspection/RESTORE-STATUS-20261007.md`: chronological findings; later sections supersede earlier incomplete conclusions.
- `device-inspection/kyocera-custom-dl-research/vendor-dispatch.txt`: saved disassembly.
- `device-inspection/kyocera-custom-dl-research/live/`: live GPT/partition reads, before/after misc bytes, write validation, TWRP entry log, completed stock restore log, and boot observation.
- `device-inspection/sahara-extended-diagnostic/boot-log.txt`: current SBL log from RAM. Confirms SD trigger and Sahara entry; it is not a normal-boot crash log.
- Owner signing private key exists locally; **never print it, disclose it, or upload it to a service**.

If stock Android still loops, return to verified TWRP using the same misc request and collect pstore/recovery/Android logs. Validate causes before restoring data or changing additional partitions. Always distinguish verified firmware writes, successful recovery boot, and verified normal Android startup.

Primary research lead: https://jtechforums.org/t/kyocera-e4810-bootloader-unlock-and-root-guide/6167/126 and https://forums.jtechforums.org/t/can-you-unlock-and-root-kyocera-e4810/4227/140. Their attachment downloads failed during this work; their scripts were not executed. The working KYF37 transport was derived from the local stock SBL and tested on this phone.

