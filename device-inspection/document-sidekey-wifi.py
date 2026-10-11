from pathlib import Path
p=Path('KYF37-SECONDARY-SCREEN.md')
p.write_text(p.read_text(encoding='utf-8')+'''

## Side-key mapping fix — 2026-10-08

The owner confirmed that closing the lid and pressing the side key now lights the outer clock. Raw input from `qpnp_pon` (`/dev/input/event2`) is Linux scan code **254**, mapped to Android **CAMERA** by `qpnp_pon.kl` (also present in `gpio-keys.kl`). PhoneWindowManager intercepts a physical CAMERA press with the lid closed and starts OuterScreenService using `org.kyf37.action.OUTER_WAKE`; it consumes the key so the main screen stays asleep.

Android 10 key layouts do **not** accept the old `WAKE` or `WAKE_DROPPED` flags. Their presence made the entire OEM layout fail parsing, and EventHub fell back to Generic.kl. This broke the side key and other board-specific key assignments. Remove these flags from all board layouts; implement wake behavior in framework policy and the kernel wake IRQ instead. Do not re-run older scripts that add WAKE flags.

Verified after one zygote restart: EventHub selected `qpnp_pon.kl`, `matrix_keypad_67.kl`, and `swic_hs_key.kl`. Owner then verified the side key. Corrected files were persisted on `/system/usr/keylayout/`, not left as temporary bind mounts; originals are in `/data/local/tmp/kyf37-keymap-wifi-backup/`. System was synced and remounted read-only. The ROM source and rebuilt system image contain the same corrected layouts. A reboot-based verification is still required.
''',encoding='utf-8')
p=Path('HANDOFF-ANDROID10-KYF37.md')
p.write_text(p.read_text(encoding='utf-8')+'''

## 2026-10-08: side key fixed; Wi-Fi UI restored, hardware still fails

- Owner recorded closed-lid side key: event2 (`qpnp_pon`), scan254 down/up. Android10 rejected legacy WAKE flags in OEM .kl maps and fell back to Generic. Source maps fixed by `fix-android10-keylayout-flags.py`; correct maps loaded after a single `ctl.restart zygote`. Owner explicitly confirmed outer clock now wakes on side key.
- Applied maps and Wi-Fi/wifi.direct feature XML permanently to existing `/system`, preserving original maps in `/data/local/tmp/kyf37-keymap-wifi-backup/`; synced and restored system RO. No full ROM or boot flashed. Source image rebuilt successfully in 54 seconds before later startup-helper changes.
- WifiService, WifiScanner, WifiP2p now registered. Settings WifiSettingsActivity and NetworkDashboardActivity explicitly re-enabled because previous missing feature had persisted disabled components. `android.settings.WIFI_SETTINGS` now opens actual Wi-Fi page. No successful scan/association.
- Current V8 system had no wcnss_service at all. Ran exact stock executable from `/data/local/tmp/wcnss_service-stock` as root, process19227, foreground adb session2762. It blocks waiting for firmware calibration; QMI initialization fails. Preserve existing calibration/NV.
- WCNSS subsystem was ONLINE but WCNSS_CTRL.6 and WLAN_CTRL.6 platform devices were unbound: probe had run before userspace trigger and returned ENODEV. Actual binds through each driver's bind sysfs file restored real channel probes. Firmware version became 01050102, build00104. NV download produced actual WCNSS_NVBIN_DNLD_RSP status2 (WAIT_FOR_CBC_IND). Never fake nv_downloaded/is_cbc_done or bypass readiness checks.
- Missing `/data/misc/wifi/WCNSS_qcom_wlan_nv.bin` was seeded only when absent using exact OEM `/system/etc/wifi/WCNSS_qcom_wlan_nv.bin` (same as JPN stock default, SHA df1ee7e3bdc465055c5bac23f579ab6a0ae21a326a95e7b117e8fbb3676806d6), system:wifi 0660, restorecon. This is an OEM default, not recovered per-device factory calibration. Kernel default fallback already exists, but WLAN host driver specifically requires primary filename. No modem/persist/factory NV altered.
- Driver now parses NV version3 but WDI start fails with firmware status38. `wlan-prima-caf-123/riva/inc/wlan_status_code.h` enumerates this as eHAL_STATUS_WLAN_BOOT_TEST_FAILURE. CBC completion not observed. wlan0 never appears. Do not claim working Wi-Fi, invent calibration or treat permissive SELinux logs as the load failure.
- A WCNSS_CTRL unbind/rebind returned EAGAIN initially; bind succeeded after peer closing handshake. Do not repeat indiscriminately. Only this Wi-Fi control driver touched; no subsystem reset invoked.
- Source staged exact stock daemon as `system/bin/wcnss_service_stock` to avoid colliding with CAF-built wcnss_service. init.target.rc service uses stock filename. `kyf37-wifi-init.sh` seeds absent OEM default and retries real unbound WCNSS/WLAN platform probes for at most30seconds, exits once bound. Source wrapper `stage-wcnss-startup-fix.py`. Cold-boot helper/hardware not yet verified. Later build started PID28184; inspect `/home/pablo/kyf37-android10-build.log` before starting another.
- Removed redundant firmware_directories append: current ueventd already searches /etc/firmware (= /system/etc/firmware), and logs prove default firmware loads.
- debug.hwc.kyf37_sync_wait is0. GPU tearing remains unresolved; first force-client-composition test owner reported still tearing. Later sync test no owner verdict. Other live native/codec binds remain as earlier notes.
- Just after svc wifi disable, ADB disconnected; unknown whether owner unplugged or device changed state. Async question pending asking whether Android/asleep/TWRP/logo. Do not infer crash. trial-return service last checked stopped. Source changes/new full image NOT flashed.
''',encoding='utf-8')
