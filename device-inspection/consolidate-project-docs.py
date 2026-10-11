"""Archive superseded root notes, then publish one current project guide. No secrets read."""
from pathlib import Path
import hashlib, json, zipfile

root = Path(__file__).resolve().parent.parent
archive = root/'kyf37-rom/documentation-history-20261011.zip'
sources = sorted(p for p in root.glob('*.md') if p.name not in ('AGENTS.md', 'KYF37-PROJECT.md'))
if not archive.exists():
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        records = {}
        for p in sources:
            data = p.read_bytes()
            records[p.name] = hashlib.sha256(data).hexdigest()
            z.writestr(p.name, data)
        z.writestr('manifest.json', json.dumps(records, indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    records = json.loads(z.read('manifest.json'))
    for name, digest in records.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == digest
    recovery = z.read('KYF37-USB-RECOVERY-RUNBOOK.md').decode('utf-8-sig')
guide = '''# KYF37 Android 10 — current project guide

Updated 2026-10-11. This is the authoritative current-state guide. Historical notes are preserved byte-for-byte in `kyf37-rom/documentation-history-20261011.zip`, with an independently checked SHA-256 manifest. Old assertions in that archive describe their dates, not today's state. Component artifact READMEs remain local evidence and rollback instructions.

## Device, safety and workspace

Kyocera GRATINA KYF37: MSM8909 / Adreno 304, ARM32 Cortex-A7, approximately 1 GB RAM, 480×854 non-touch panel, D-pad/keypad, 128×36 outer screen. Android 10 QQ3A.200805.001 / LineageOS 17.1 on OEM Linux 3.10.49. Installed recovery is owner-signed TWRP 3.7.0_9-0 with the keitai D-pad UI (display-fixed image), installed on explicit owner request 2026-10-11. Full recovery readback matched c7f5a41565595607a10930ddb174f9755568c01156a6440c34abdb5cca25141d; menu framebuffer and navigation logs checked. Android subsequently booted. Prior TWRP is backed up at phone-backup/keitai-test/recovery-twrp-backup.img and on SD. A 2026-10-09 bootslot-passed.flag records earlier owner-confirmed keys; the prior host-only summary was stale.

Windows workspace: `C:/Users/pablo/Documents/ChatGPT/flipphone_roms`; WSL Ubuntu source: `/home/pablo/kyf37-android10`; kernel: `/home/pablo/kyf37-rom/kernel-android10`; stock source: `/home/pablo/kyf37-rom/stock-system`. ADB: `C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe`; always target serial `981108631314`.

Never write recovery, keystore, modem/persist/NV or wipe userdata. Preserve `phone-backup/`, `device-inspection/system-stock.img`, the entire `kyf37-twrp-device/`, stock images and SD rollback directories. The owner private signing key must never be printed, copied, hashed or uploaded; invoke the signing script instead. Boot signatures must match the enrolled owner keystore. Do not flash OEM boot alone with that keystore installed.

One build tree and one phone are shared. Serialize builds through `device-inspection/build-locked.sh`; hardware mutations require `tools/phone-lock.ps1 acquire <name> <minutes>` and release afterward. Check `status` first. No competing input, camera, radio or performance tests. Never reset host USB or read unsafe mdss debugfs `panel_reg` / `base_reg`; no speculative DIAG or /dev/mem writes.

## v22 release and what changed

v22 packages the current source, including changes that were previously installed as application/library updates after v19/v20. Consult `kyf37-rom/v22-validation.json` for the final package result; release creation and previous live component tests do not establish a v22 boot test. The package does not flash itself or reboot the phone.

Included refinements: Kyocera Classic (Appearance key 3), the supplied blue sky/castle wallpaper as the real handset framework default, persistent launcher folders and correct folder focus return, readable wallpaper-dependent text, explicit Camera2 pinning without a resolver/duplicate camera tile, native Pixel-style lock clock, native D-pad Settings and notification controls, current stock-app compatibility, working brightness HAL placement, current outer-screen video/audio, and SIM/mobile-data libril compatibility. v22 additionally verifies packaged lights HAL and libril hashes against build output to catch stale integration.

Existing user wallpaper/theme/folder preferences survive updates; a new default wallpaper does not overwrite an owner's previously selected wallpaper. The theme installer can explicitly apply the supplied wallpaper to Home and lock screen without flashing.

## Fixes, root causes, reproduction and verification limits

| Area | Finding and correction | Reproducible source / evidence |
|---|---|---|
| Brightness | Android 10's vendor HIDL loader could not use the unstaged lights module. Mark `lights.kyf37` vendor, include its Android.mk and set `ro.hardware.lights=kyf37`. Settings changes now reach both LCD backlight nodes. | `fix-android10-brightness.py`; live values 40 and 180 matched both nodes; restored 10. Physical luminance was not independently measured. |
| Settings D-pad | Secondary switch widgets and master switch bars needed explicit keyboard focus/action handling; skip categories and guard a missing USB service. | `fix-android10-settings-dpad.py` and navigation scripts; live Location 3→0→3 and Captions 1→0, not every Settings page. |
| Native focus/shade | Native Views/list rows and QS tiles lacked obvious focus or spatial movement. Add visible outlines, spatial selection, OK actions and numbered native tiles. Remove obsolete generic footer globally; supported stock apps keep their own guides. | `fix-android10-visible-focus.py`, `fix-android10-keypad-panel.py`, later `focus-theme`, `keypad-nav-ui`, `systemui-shade`, `systemui-material`, `native-only-bars` scripts; latest build wrapper order wins. |
| Lockscreen | Replace enclosing clock card with large stacked idle clock, compact notification clock and native authentication/actions. D-pad invokes the normal credential flow. | `fix-android10-modern-lockscreen.py`; previous live screenshots and native keyguard tests. No credential bypass. Material-inspired styling is possible on Android 10; Android 12 Monet is not present. |
| Launcher folders | Store component IDs in SharedPreferences, seed Kyocera ports, open/close with D-pad/OK/Back, expose management with `*`. Record selected tile on folder activation, including numeric activation. | `fix-android10-home-folders.py`, `Kyf37HomeFolders.java.inc`; 8-member folder, numeric 6, Back focus and cold restart persistence tested. Full create/rename/remove text entry and physical long-OK are not exhaustively verified. |
| Themes/wallpaper | Standard=0, Pastel Star=1, Sky Star=2, Kyocera Classic=3 via `Settings.Global.kyf37_icon_theme`. 80 Classic assets, 53 directly extracted semantic stock glyphs; remainder use stock fallback artwork. Device-only wallpaper overlay lost to Lineage common overlay; stage handset nodpi/hdpi at both overlay sources. | `prepare-kyocera-classic.py`, `fix-android10-kyocera-classic.py`, `kyf37-rom/kyocera-classic/verify-pack.py`; three APK hashes match live installs, four choices rendered, exact final framework wallpaper pixels checked. |
| Original app icons | Unmapped packages and placeholder generic mappings previously replaced real activity icons. Theme loader now returns no override for unmapped, missing or corrupt artwork; Home loads the original activity icon in both root tiles and folders. | `fix-android10-original-icon-fallback.py` runs after Classic staging; `verify-original-icon-fallback.py` exercises the Java loader for all three themes and cache reuse. |
| Build branding | Displayed build name uses althia and omits the test-keys suffix; actual signing tags remain accurate. Live build.prop and resetprop applied, then persistence confirmed after recovery round-trip reboot. | `fix-android10-build-branding.py`, `tools/apply-build-branding.ps1`; source wrapper exports BUILD_USERNAME=althia; generated buildinfo validation passed. |
| Ambient light | KYF37 official manual confirms an ambient-light sensor for automatic brightness. Current v22 sensorservice exposes only the accelerometer; ambient-light HAL integration remains missing. | `kyf37-rom/sensor-check.txt`; official au KYF37 detailed manual, printed page 16. |
| Camera shortcut | Implicit camera intent resolved to Android ResolverActivity, producing a generic tile and a duplicate. Pin Camera2 explicitly if installed, otherwise Kyocera Camera. | Classic staging / `Kyf37Home.java.txt`; live single root Camera, stock Camera retained in folder. |
| Wi-Fi | Legacy init shadowed HIDL supplicant. Kernel 3.10 netlink attribute 204 collides with IFACE_SOCKET_OWNER; skip it, terminate failed roaming callbacks. Gateway policy routing requires RTNH_F_ONLINK. | `fix-android10-radio-wifi.py`, `fix-android10-wpa-supplicant-hang.py`, `fix-android10-netd-onlink.py`; association, DHCP, DNS, HTTPS and Android validation hardware verified. Do not redo solved Wi-Fi. |
| SIM status | Stock qcril returns 284-byte card status with seven header words; Android 10 expects 280/six. Convert header/array with bounds checks instead of accepting length blindly. | `fix-android10-ril-cardstatus.py`; owner PIN prompt and SIM state survived reboot. Agent must never enter or guess SIM PIN. |
| Signal/mobile data | qcril reads optional data[7]/data[8] while modern libril allocated seven pointers, causing strcat SIGSEGV and radio proxy restarts. Allocate two additional zeroed entries without changing request length. | `fix-android10-ril-setupdata.py`; rild stable and 62/62 five-second service samples; Movistar GPRS validated, interface-bound ping/DNS/HTTP with Wi-Fi off. Full reboot after this latest fix, LTE, calls, SMS and IMS/VoLTE remain unverified. Earlier 'no NAS/DATA port' conclusions are superseded. |
| Camera HAL/JPEG | Restore AE/AWB Cipo libraries and tuning files, fix kernel session routing/malformed notifications, daemon label/start order and HIDL memory cookie. Preload JPEG compatibility shim for legacy symbols, perf-null/backtrace and mutex semantics. | Camera fix scripts and `libkyf37_jpegcompat`; both Camera2 and stock app saved JPEGs after cold boot. Video recording unverified. |
| Storage/JIT | Backport sdcardfs per-view mounts and memfd_create to kernel #17; JIT now works and external storage mounts under `/storage/<uuid>`. | `apply-kyf37-kernel-fixes.sh`; GCC 4.8 only. Rebuild wlan/core_ctl for every kernel change through `build-kyf37-modules.sh`; symbol CRC mismatch otherwise removes Wi-Fi. |
| Stock apps | Deodex, add Kyocera compatibility dex/stubs, remap private resources, replace old removable-storage APIs and restore app-native guide contracts. | `port-stock-apps-android10.py`, `build-kyocera-compat-dex.py`, `patch-kyocera-compat-smali.py`, `fix-android10-selected-stock-runtime.py`, `fix-android10-stock-storage-api.py`. Not all 53 audited candidates are production-ready. Memo editor remains a runtime concern. |
| Dialer | Native keypad Phone/Messages/Contacts supplied; experimental `org.kyf37.dialerxx` still lacks OEM Telecom/provider APIs. | `fix-android10-keitai-apps.py`; retain native default, do not select experimental stock dialer as default. Calls/SMS need separate hardware tests. |
| Audio | Stock HAL pcm_config is 36 bytes while Android 10 tinyalsa expects 40; avail_min became invalid silence_size and SW_PARAMS failed. Correct only legacy pcm_open ABI. | `fix-android10-audio-pcm-config-abi.py`; guarded allocations/build/persistent live hash verified; advancing speaker PCM and DAC On, no direct listening claim. |
| Outer display | Bounded character scenes, timeout/settings, side hold 0.8s Bad Apple 15fps+music, stop/open-lid cancellation and adaptive 80–128px media framing. | `fix-android10-outer-animation.py`, `fix-android10-outer-settings.py`, `fix-android10-outer-badapple.py`, `prepare-bad-apple-wide.py`; release verifies APK/media/library hashes. Full earlier playback ended with main screen OFF and resources released; newest wide geometry has host QA, not repeated physical playback QA. |
| Lid | Default lid_behavior=1 sleeps internal display; opening can answer a ringing call and side key controls outer display when closed. | `fix-android10-lid-sleep.py`; live lid input, sleep and timeout checks. Synthetic framebuffer changes are not direct observation of physical panel darkness. |
| Flashlight | Native single large button, center toggles; Back/leaving/screen-off requests Off. | `fix-android10-keypad-flashlight.py`; hardware torch 1→0. v22 release gate caught MobileLight being rebuilt from a remaining stock prebuilt declaration. fix-android10-release-refinements.py removes that module declaration, marks the native app as its override and removes stale installed output before building. The legacy input APK is preserved for porting. Existing userdata copies may still require separate removal. |
| Boot reliability | Missing privileged permission allowlist caused system_server crash loop; stale TV/public-libraries files survived removed copy rules and broke boot. Stage allowlists and remove obsolete files from both source and output. | `fix-android10-keypad-privapp.py`, `remove-tv-apps`, `remove-kyocera-public-libs`; `check-release-image.py` gates fresh image. |

## Outer settings and performance

`Settings.Global.kyf37_outer_*` controls clock size, 12/24h, seconds, battery, timeout, animations and video. Default timeout is 10 seconds; 0 means always on. Appearance selection and folders persist across APK/ROM updates. Side key scenes remain bounded; lid opening cancels playback.

Low-RAM configuration, ART JIT and 384 MB zram are enabled. Home PSS was about 33 MB in the last live baseline; this is not a before/after benchmark. GPU GLES works; physical-panel tearing remains unresolved although scrcpy is clean. Do not claim triple buffering/glFinish solved it. Newer mainline/vendor kernels are not a drop-in replacement for the panel, modem, camera and keypad drivers.

Magisk v23 uses runtime-daemon mode because magiskinit boot patching does not activate in this 2SI setup; opt out with `persist.kyf37.magisk=0`. microG/Aurora remain staged. GPS engine starts and lists satellites with a foreground-authorized client; no indoor fix established, open-sky test required. Bluetooth, infrared transfers, FeliCa, One Seg and complete call/SMS/VoLTE behavior are not comprehensively validated. TV is intentionally excluded from release images.

## Rebuild and package (host only; no flash)

Keep every change as an idempotent `device-inspection/fix-android10-*.py` script. The wrapper orders native softkeys, stock compatibility, final no-footer policy, navigation/theme/radio patches, modern lockscreen, folders, Classic theme and final release hygiene. Running an older generator afterward can undo fixes. Recovered OEM resource staging now compares bytes and preserves unchanged file timestamps; its generated add-resource XML previously forced a needless framework and dependent-app rebuild on every invocation. verify-resource-staging-idempotence.py checks content and timestamps across two repeated runs.

From PowerShell at the workspace root:

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-locked.sh /home/pablo/v22-build.log
# Require BUILD_EXIT=0 in that log.
wsl -d Ubuntu -- bash /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/package-release.sh v22
python device-inspection/sign-rom-boot.py kyf37-rom/android10-go-candidate-20261007-v22/boot-android10-unsigned.img kyf37-rom/android10-go-candidate-20261007-v22/boot-android10-owner-signed.img
python device-inspection/build-twrp-android10-installer.py v22
```

Packaging requires release boot (never diagnostic), matching kernel/modules, e2fsck exit 0, current APK/media/native hashes, zero unresolved installed vendor symbols, owner signature/body preservation, protected-partition installer tests and release-image gates. ZIP CRCs and every payload hash are read back on the host. The legacy filename date 20261007 is retained for tooling compatibility; v22 is prepared on 2026-10-11.

Never install isolated framework.jar/framework-res/services changes on the running phone. Use a matching validated image set. App-only changes can use signed `adb install -r -d`; `/system` changes require the WP helper and a final sync/remount read-only. Git Bash needs MSYS_NO_PATHCONV=1; prefer PowerShell.

## Installing and validating a release

Use the existing TWRP and `tools/flash-release.ps1` only for an authorized flash with exclusive phone lock. Keep at least 1.7 GB SD free beyond the ZIP for backup. The installer checks serial, geometry, source hashes and protected partition hashes, saves current boot/system under `/external_sd/KYF37-Android10-rollback-*`, writes system then owner-signed boot and fully reads back both. It never wipes userdata, replaces recovery, changes modem or reboots automatically. ZIP signature verification is disabled for the unsigned installer ZIP; the contained boot is independently owner-signed.

Wait for successful installation before rebooting. If it fails, stay in TWRP and restore both matching backup images; never boot a partly written image pair. Preserve the SD rollback directories. After boot require sys.boot_completed=1, expected focused window and screenshot, no new FATAL EXCEPTION, side/lid/keypad behavior and more than 15 minutes uptime without recovery return. Separately test brightness, SIM owner unlock, radio/data, native dialer and camera. Report hardware tests separately from host validation.

## Workspace cleanup policy

The earlier cleanup removed 30.92 GiB of regenerable caches and superseded staging images. v22 cleanup retires pre-v19 installer ZIPs and v19/v20 duplicate raw/sparse staging images only after validating v22 and both retained rollback ZIP payloads. Retired pre-v19 candidate metadata is preserved in kyf37-rom/retired-release-metadata-20261011.zip; obsolete candidate boot images and intermediate SystemUI test APKs are retired. Stock/recovery assets, signing directory, source/artwork/build inputs, current v22 candidate, v19/v20 ZIPs, before-APKs, original SystemUI rollback and SD rollbacks remain. Exact file deletions and reclaimed bytes are recorded in device-inspection/cleanup-result-v22.json; the archived root notes retain all previous findings. No WSL tree or phone storage is cleaned by this operation.

## Recovery and fault isolation

Unexplained resets can corrupt ext4. Capture last_kmsg/recovery logs; TWRP itself can panic within four seconds when userdata has errors=panic. `device-inspection/fastcap.py` captures logs and `fsck-race.py 120 -fy` stops TWRP and repairs data; recheck cache. Do not wipe or format data. A legacy recovery guard occupies misc bytes 0–31; clearing only those bytes from verified TWRP removes boot-recovery without overwriting other fields. Release boots omit the diagnostic timer/guard.

The full independently verified USB/stock recovery procedure is retained below verbatim. Its historical incident dates are evidence, not the current Android release status.

'''
status = root/'kyf37-rom/v22-validation.json'
if status.exists():
    release = json.loads(status.read_text())
    assert release['revision'] == 'v22' and release['zip_crc_and_payload_hashes_verified']
    current = ('## Current release result\n\n'
               'v22 is built, owner-signed and packaged. Filesystem, kernel/module ABI, 193-file vendor symbol audit, '
               'required/forbidden image assets, theme/wallpaper, nine installer safety cases and complete ZIP payload/CRC checks passed. '
               '**Not flashed; integrated v22 hardware boot remains unverified.**\n\n'
               f"Installer: `kyf37-rom/{Path(release['zip']).name}` ({release['bytes']:,} bytes). "
               f"SHA-256: `{release['sha256']}`. Detailed final report: `kyf37-rom/v22-validation.json`.\n\n")
    hardware = root/'kyf37-rom/v22-hardware-validation.json'
    if hardware.exists():
        live = json.loads(hardware.read_text())
        current = current.replace('**Not flashed; integrated v22 hardware boot remains unverified.**',
            'Flashed and booted on 2026-10-11; installer readback/protected-partition checks passed, userdata preserved. '
            'Home/wallpaper/folders and brightness nodes checked. Movistar GPRS internet ping passed; Wi-Fi reconnection unresolved. '
            'See kyf37-rom/v22-hardware-validation.json and v22-flash.log. Rollback: ' + live['rollback'])
    cleanup = root/'device-inspection/cleanup-result-v22.json'
    if cleanup.exists():
        result = json.loads(cleanup.read_text(encoding='utf-8-sig'))
        current += (f"Cleanup applied: {len(result['files'])} obsolete files, "
                    f"{result['bytes']/1024**3:.2f} GiB removed, "
                    f"{len(result['removed_empty_directories'])} empty candidate directories removed; "
                    'stock assets and v19/v20 rollback ZIPs retained. Old root notes and candidate metadata are checksummed in their history archives.\n\n')
    guide = guide.replace('## Device, safety and workspace',current+'## Device, safety and workspace',1)
(root/'KYF37-PROJECT.md').write_text(guide + recovery.replace('# KYF37 bootloop recovery: confirmed USB procedure', '## Verified USB recovery procedure (historical incident, still applicable)', 1), encoding='utf-8')
# Keep AGENTS concise and point new work to the authoritative guide.
(root/'AGENTS.md').write_text('''# KYF37 project entry point

Read `KYF37-PROJECT.md` first: current state, root causes, reproducible fixes, build/release workflow, validation limits and full USB recovery procedure. Historical root notes are checksummed in `kyf37-rom/documentation-history-20261011.zip`; component artifact READMEs retain detailed logs/rollback evidence.

Mandatory: no recovery/keystore/modem/persist/NV writes or userdata wipes. Never read, print, copy, hash or upload the owner signing private key. Preserve stock backups, `phone-backup/`, `kyf37-twrp-device/` and SD rollback folders. Builds only through `device-inspection/build-locked.sh`; phone mutations only under `tools/phone-lock.ps1`. Keep source edits in rerunnable fix scripts. Do not claim an unflashed release is hardware verified. No speculative USB resets/debugfs register access. Keep native authentication and the native default dialer.
''', encoding='utf-8')
# All deletions occur only after complete archive readback verification.
for p in sources:
    assert p.parent.resolve() == root.resolve()
    assert hashlib.sha256(p.read_bytes()).hexdigest() == records[p.name]
    p.unlink()
print(json.dumps({'archived_root_documents': len(records), 'guide': str(root/'KYF37-PROJECT.md'), 'archive': str(archive)}))
