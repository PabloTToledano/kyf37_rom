# KYF37 cellular/LTE investigation and repair plan

Investigation date: 2026-10-08. Status: offline diagnosis and proposed repair; no modem fix has been applied or verified.

The strongest identified blocker is a repeatable **radio daemon crash during Qualcomm peripheral-manager registration, before Android's radio service can finish starting**. The packaged v13 still contains the same `libbinder` and `rild` build IDs implicated by the saved crash logs. Repair this startup path first. APN changes and LTE-band changes cannot repair this crash.

The saved logs also establish a second problem: the modem is reported offline and its SMD control channel cannot be opened. This might follow from the failed peripheral-manager client lifecycle, or might be a separate modem bring-up failure. The existing evidence does not establish that fixing the crash alone will restore LTE.

## Scope and release identity

Examined the latest packaged candidate found in the workspace: `kyf37-rom/android10-go-candidate-20261007-v13`. The corresponding distribution is `kyf37-rom/kyf37-android10-go-20261007-twrp-v13.zip`. The current Android source/output has newer timestamps; it must not be treated as an exact description of the packaged release.

| Immutable input | SHA-256 |
| --- | --- |
| v13 `system-android10.raw.img` | `1d1e38d1406ab46e13617e9a01b46b6ef9bbbe8f514bfe2beb8e5b06ee78368f` |
| v13 unsigned boot image | `b6a68e08c36b67a743f1444af96de5138d38e2547d88fd27f4eddade0033f4ad` |

The image hashes were checked before inspection. Files were extracted using read-only `debugfs` operations; the boot ramdisk was parsed locally. All investigation outputs are in this new `modem-investigation` folder. No ADB commands, phone access, flashing, physical testing, protected-partition changes, signing-key access, or edits to the existing ROM/source folders were performed.

The installed version on the phone is not established by this investigation. Runtime evidence comes from **saved v7/v8 logs**, not a new v13 run. Matching packaged binaries makes the evidence relevant to v13, but does not prove that every earlier symptom occurs on the current phone.

## Findings ranked by confidence

| Finding | Evidence and confidence | Consequence |
| --- | --- | --- |
| `rild` crashes inside the peripheral-manager registration path | Confirmed in saved tombstones/logs; 37 files in `v7-second-tombstones` contain the same fault address | Radio startup does not complete |
| v13 retains the implicated code | Confirmed ELF build IDs for `libbinder` and `rild`; stock/v13 Qualcomm peripheral and QCRIL blobs have identical hashes | There is no binary evidence that v13 repaired this path |
| Failure involves invalid C++ virtual dispatch in `asBinder()` | Confirmed by matching crash offset and disassembly | Investigate object construction, layout, ownership and compatibility, not just exported symbol names |
| A broader old/new Binder C++ compatibility defect causes the bad object | Strong working hypothesis; exact corruption origin unproved | Needs an isolated reproducer before choosing a shim or replacement |
| Modem control transport is unavailable | Confirmed saved `ENODEV` and `DATA5_CNTL open failed -19` | After daemon repair, modem boot/channel availability remains a separate gate |
| Lost QCRIL peripheral vote explains the offline modem | Plausible, not established | Preserve real power-vote semantics; reassess after registration works |
| Missing RFS namespace still causes the original v6 panic | Original failure documented, but v13 contains the inspected MPSS links and firmware mount correction | Preserve the existing correction; do not assume it guarantees successful runtime firmware access |
| APN, SIM provisioning, RF bands or IMS are the first cause | Not supported by the crash evidence | Investigate only after radio/transport startup works |

## 1. The decisive crash

`device-inspection/v7-second-tombstones/tombstone_00` records `SIGSEGV`, fault address `0x20300868`, in `/vendor/bin/hw/rild`, UID 1001:

```text
unknown address 0x20300868
libbinder.so: android::IInterface::asBinder()+10
libperipheral_client.so: android::pm_register_connect(...)+242
libperipheral_client.so: pm_client_register+190
libril-qc-qmi-1.so: qmi_ril_peripheral_mng_init+400
libril-qc-qmi-1.so: qcril_qmi_load_esoc_and_register_with_pm+358
libril-qc-qmi-1.so: RIL_Init+48
rild: main+522
```

The v13 `libbinder.so` build ID is `4b287b279610c091d901a70297a941c7`; its legacy member `asBinder()` is at Thumb address `0x3848d`. The saved tombstone reports the same build ID and offset. The v13 `rild` build ID is `f44457fa845f51b9f49bdcb9e4bef79e`, also matching the tombstone.

The v13 disassembly at `0x38496` executes `blx r2`, after loading `r2` from `[vtable + 8]`. At the crash, `r2` and PC are both `0x20300868`. This is an invalid virtual call target. It is not a failure to resolve the `asBinder` export: the call successfully reaches that export and fails during dispatch through the supplied object.

The peripheral caller at `0x670e` passes the interface stored at client offset 24 to this member method. Trace the object from that field backwards through service lookup, interface casting and construction. The exact point at which its pointer/vtable becomes invalid has not been established.

Important qualification: the OEM stock `asBinder()` also dispatches through vtable offset 8 and uses the same ARM hidden-return-pointer convention. Therefore these disassemblies **do not prove that changing the virtual slot number or adding an ARM calling-convention wrapper is sufficient**. A null guard would not address this observed non-null invalid target either. The old and new surrounding C++ implementations and object lifetimes must be examined.

The source compatibility addition is in `device-inspection/integrate-android10-remaining-native-compat.py`, which adds the member method to Android 10 `frameworks/native/libs/binder/IInterface.cpp` and its header. An export audit with zero missing symbols does not validate object layout, constructors, virtual inheritance, `RefBase` ownership, `Parcel` layout or transaction compatibility.

For comparison, [AOSP Android 7.1's compatibility entry points](https://android.googlesource.com/platform/frameworks/native/%2B/android-7.1.1_r11/libs/binder/IInterface.cpp) explicitly construct the return smart pointer and forward to the static method. That is a useful reference for a controlled ABI experiment, not evidence that substituting it will cure this crash.

## 2. Modem offline and SMD transport failure

Saved `v7-first-logcat.txt` shows the peripheral manager adding QCRIL while the modem is offline, followed immediately by the SIGSEGV. Later it removes the dead QCRIL client. Saved `v8-final-cache-logcat.txt` repeatedly reports:

```text
Unable to open port id /dev/smdcntl0, error [19:No such device]
```

Saved kernel logs also show `DATA5_CNTL open failed -19`. In the current kernel's `drivers/char/msm_smd_pkt.c`, this message follows failure of `smd_named_open_on_edge()`. This concerns opening the modem's advertised channel; the existence of a device node does not establish that the remote channel is available. Error 19 is `ENODEV`, not the permission-denied error `EACCES`. Broad chmod changes or disabling SELinux are not supported repairs for this message.

Distinguish the two failure stages in subsequent evidence:

1. Did QCRIL register its peripheral client and obtain/retain a genuine modem power vote?
2. Did modem firmware complete boot, without a subsystem restart or fatal RFS/TFTP error?
3. Did MPSS publish `DATA5_CNTL` and did QMUX open it successfully?

A captured chronology spanning all three is required to attribute transport failure to the crash. Existing v8 excerpts also contain transport failures outside the immediate crash sequence; this report does not assert a proven single cause.

## 3. What v13 already contains

The packaged ramdisk mounts the existing modem partition read-only at `/firmware` with `kyf37_firmware_file` context. It starts `per_mgr` as `/system/bin/pm-service` in class `core`. `rmt_storage` has a service declaration and a start trigger in `init.target.rc`; its `disabled` declaration alone does not mean it never runs.

Read-only image inspection verifies these MPSS paths:

```text
/system/rfs/msm/mpss/readwrite          -> /persist/rfs/msm/mpss
/system/rfs/msm/mpss/readonly/firmware -> /firmware
```

The inspected directory also contains `hlos`, `ramdumps` and `shared`. This supports inclusion of the previous RFS repair. It does not validate live target mounts, permissions, contents, every RFS link, or daemon behavior. Preserve the OEM layout; do not create fabricated calibration/NV data or redirect persistent modem storage to an empty directory.

The radio service exists under **`/vendor/etc/init/rild.legacy.rc`**, naming `ril-daemon` and `/vendor/bin/hw/rild`, user `radio`. Absence of files named merely `rild.rc` was checked and is not a missing-service diagnosis. Future monitoring must use the actual service name.

The packaged properties select `/system/vendor/lib/libril-qc-qmi-1.so` for both legacy and vendor RIL paths; the ramdisk supplies `-d /dev/smd0`. The VINTF manifest declares `android.hardware.radio@1.1::IRadio/slot1`, matching the inspected Android RIL service implementation. No evidence currently identifies the manifest version as the startup blocker.

## Recommended implementation order

### A. Reproduce and locate the C++ corruption offline

Create a separate source/build copy before changes. Add rerunnable `device-inspection`-style patch scripts in that new work area. Keep an untouched v13 baseline and hashes.

Build a small ARM Android test client with the packaged libraries that exercises peripheral service lookup and interface conversion. Use an Android guest/emulator with a mock peripheral-manager service where necessary; a generic Linux ARM executable alone cannot reproduce Android Binder IPC. A mocked service can test object creation/dispatch and error handling, but cannot prove modem operation.

Trace client field 24, the interface pointer, its vtable and slot 8 at creation and immediately before `asBinder()`. Check `IPeripheralManager`/`BpInterface` construction, virtual base offsets, `BpRefBase` and `RefBase` layouts, reference acquisition/release and any preceding `Parcel` operation. Compare against the OEM binaries/headers. Use the correct Thumb addresses and modern ELF relocation tooling: old GCC 4.8 objdump PLT labels on a modern linked library must not be used alone to infer which imported reference-count function a call reaches.

Acceptance: a valid executable call target, correct smart-pointer ownership through repeated register/unregister and service-death cycles, and reproducible failure handling. A successful link or missing-symbol audit is insufficient.

### B. Replace the fragile peripheral-manager boundary

Preferred repair, if the matching Qualcomm source can be obtained: rebuild **both** `libperipheral_client` and `pm-service` against the same Android 10 Binder/utils headers and libraries. Keep the C `pm_client_*` ABI used by the proprietary QCRIL blob, including callbacks, error returns, client handles and lifetime rules. Preserve service descriptors, transaction IDs and parcel formats if any legacy peer remains. The local vendor trees inspected contain the proprietary client blob, not an obvious matching peripheral-manager source implementation.

If source is unavailable, reconstruct a narrow compatible client bridge around the exported C peripheral API and communicate with a deliberately defined service boundary. This is implementation work requiring tests of all QCRIL-used exports and real vote semantics. A confined legacy runtime is another engineering option, but isolation and dependencies must be proven; mixing old and modern C++ Binder objects in one namespace recreates the problem.

Do not replace the system-wide Android 10 `libbinder.so` or `libutils.so` with the stock Android 5 libraries. Do not skip `pm_client_register`, return invented success, remove the client death handler, or force the modem permanently online: these can break modem ownership and power management without restoring a usable transport.

Keep peripheral manager and its clients on the same Binder context. [AOSP documents that Binder domains are isolated](https://source.android.com/docs/core/architecture/hidl/binder-ipc). Moving only one endpoint to `/dev/vndbinder` cannot repair communication. The historical logs demonstrate that a peripheral service was reached, so a context mismatch is a check for the proposed repair, not the proven explanation for the recorded crash.

### C. Verify actual modem bring-up after the client path is stable

Preserve the firmware mount and RFS corrections. Check source/package parity for `rfs_access`, `tftp_server`, `rmt_storage`, `qmuxd`, `per_mgr`, their init triggers, user/groups, executable labels and policy. Check modem loader/subsystem-restart and SMD code against the known-working stock configuration. Attribute any remaining failure to a specific boot error, service failure or missing channel before changing the kernel.

Do not write modem/persist/NV partitions, wipe userdata, reset provisioning, replace firmware with an unrelated MSM8909 build, or flash recovery. The earlier isolated performance kernel was never installed and cannot explain the saved phone crashes.

### D. Finish Android radio integration, then LTE configuration

After `RIL_Init` returns, check the returned `RIL_RadioFunctions` version and layout against `RIL_register` and Android 10 compatibility paths, including request/response/unsolicited conversions. Confirm the `slot1` radio instance registers and that SIM status, radio power, registration state and data calls reach the framework. These stages were not reached by the recorded startup crash; further incompatibilities may become visible once it is repaired.

Only then diagnose SIM subscription mode, carrier selection, supported RF bands and APNs for Spain. Preserve stock `NV,RUIM` initially; change subscription behavior only with concrete evidence for this variant. Existing APN XML presence is not proof that the intended carrier entry is selected. A software LTE-band mask does not add RF hardware support, and current band provisioning was not read from the phone.

Treat IMS/VoLTE separately: getting LTE packet data working does not establish IMS registration or voice calling. The project currently records IMS as unverified/unported. Do not claim calls or VoLTE fixed from signal bars or an LTE data connection.

## Validation gates and limits

Offline work can validate repeatable builds, ELF dependencies, C ABI exports, Binder dispatch/ownership in a suitable guest, VINTF/init/property consistency, RFS links, firmware labels in packaged policy, and installer protection/rollback. Build, image validation and vendor-symbol audits remain required for a repair candidate. Use release boot packaging, not a diagnostic boot with a timed recovery return.

Actual modem boot, SIM detection, carrier registration, calls and mobile data cannot be certified offline. **No physical-phone validation is authorized in this task.** A later hardware validation stage would require a changed user instruction. Its acceptance criteria should be: stable `ril-daemon`/peripheral clients, modem online without fatal/SSR loops, working QMUX channel, registered radio HAL, readable SIM, carrier registration, a data call and separately tested voice/IMS. Preserve stock rollback throughout.

## Evidence and reproducibility

- `artifact-inspection.json`: verified image hashes, extracted-file hashes, ELF build IDs and dependencies, ramdisk input hashes.
- `additional-evidence.json`: packaged service declaration, MPSS symlink targets, focused disassemblies and repeated fault count.
- `elf/`: ELF symbol/dynamic records and focused disassembly files. Proprietary artifacts stay local under `artifacts/`.
- `inspect-offline.py` and `inspect-details.py`: repeatable host-only inspection scripts; run with WSL Python, writing only beneath this report folder.
- Original saved runtime evidence: `device-inspection/v7-second-tombstones/tombstone_00`, `v7-first-logcat.txt`, `v8-final-cache-logcat.txt`, `v8-camera-test-last-kmsg.txt`, and the RFS/modem history in `HANDOFF-ANDROID10-KYF37.md`.

Recommended first engineering task: isolate and repair the peripheral-manager C++ object/ABI boundary, then determine whether its corrected vote lifecycle restores the modem transport. This report provides a repair route; it does not represent a completed or hardware-verified modem fix.

## Added investigation: original TV tuner support

The TV support investigation and app attempt are in [tv-tuner/README.md](tv-tuner/README.md). The original receiver is One Seg; `FsDtvApp` is its actual app, while `TVConnect` is a different feature. The inspected v13 lacks the TV app, native service/libraries and assets. Restoration needs compatibility work on the old native Binder/media/graphics interfaces plus the existing power/SPI/I2C path and service policy. This is separate from the cellular modem fix.

A newly authored, compiled Android 10 keypad launcher/support checker is available as `tv-tuner/dist/Kyf37Tv-debug.apk`; it delegates viewing to the original app. It is not a completed receiver implementation. The stock preparation script reconstructs the OEM app from deodexed code and stages its backend for review. Build/static evidence and remaining integration gates are in the TV report. No physical-phone testing or existing ROM-folder modification occurred.
