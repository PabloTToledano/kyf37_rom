# FeliCa / Kyocera app readiness audit - 2026-10-09

Offline check only; no phone, chip initialization, provisioning or payment changes.
Reproduce: device-inspection/audit-felica-stock.py. Inventory report:
kyf37-rom/felica-audit.json.

All stock Kyocera apps are NOT ported/ready. Selected camera, memo/provider,
recorder/manager and barcode Reader modules are staged. Native softkey revisions
compile but remain uninstalled/unverified. Camera photo capture has separate
hardware verification; other app workflows need individual checks. Original
dialer remains experimental; answering-machine uplink routing is unresolved.
One Seg TV is separately queued. Do not equate app assembly with full readiness.

Stock Osaifu-Keitai launcher: FeliCaInitApp,
jp.kyocera.felicainitapp.FeliCaInitAppActivity. Related stock components found:
FeliCaInit, FeliCaLock, FeliCaLockSettingService, FeliCaUeventService,
MobileFeliCaClient, MobileFeliCaSettingApp, MobileFeliCaWebPlugin,
MobileFeliCaWebPluginBoot, felicaservice and Rakuten Edy (Edy4FP).
No corresponding module APKs were found in the current Android 10 product output.
No Nfc*.apk was found there either. Stock kernel source has CONFIG_KFELICA driver
code and legacy init has FeliCa device aliases; this does not prove a working
Android 10 driver/service/payment stack. Existing UART broker compatibility for
IrDA is not a port of FeliCa payment services.

Kyocera officially lists Osaifu-Keitai support for KYF37:
https://www.kyocera.co.jp/prdct/telecom/consumer/lineup/kyf37/spec.html
That confirms the stock wallet feature, not general-purpose Android NFC reader,
writer, peer-to-peer or Google Wallet support. General NFC support is not
established by this audit; FeliCa/payment functionality is not ready in this ROM.
Further work needs dependency/JNI/daemon/permission/SELinux analysis and later
authorized read-only hardware checks before enabling or initializing the chip.

## Broad app-port continuation — 2026-10-09, still offline

All eleven wallet-related APKs above are now reconstructed as optional candidates,
including four MobileFeliCa companion apps and Edy. This does not enable the chip
or a payment service. `libjni_felica.so` resolves dependency symbol names against
the current product providers; ABI, linker namespace, device-node, UART ownership,
permissions, trust and actual transactions remain unverified.

MobileFeliCaSettingApp declares OpenMobileAPI optional. Its five referenced
OpenMobileAPI classes/service are absent from the stock framework extraction as
well; no success stubs were inserted. NextFP is recovered with an optional JAR
and exact library-name permissions XML for Edy and the emergency buzzer. FeliCaLock's
missing original artwork is included in the new named framework resource overlay.
See `kyf37-rom/all-stock-app-ports/README.md` and `readiness.md` for exact current
checks. Current product selection and phone state remain unchanged.

## Chip foundation requested - 2026-10-09 (offline)
Kernel CONFIG_KFELICA=y and kflcd already staged. Found missing kmfc UID 9000 from stock libc's identity table, validated with known root/system/radio/nfc entries; Android identity generator accepts the recovered mapping. Prepared 3 exact configuration files, 13 exact stock numeric device rules, native/shared-user/seapp identity patch and original UART-service versus infrared fallback registration gate. Scripts: inspect-stock-felica-uids.py, fix-android10-felica-foundation.py, prepare-felica-identity.py. See kyf37-rom/felica-foundation/README.md. Another session is building; no shared source patch applied, chip initialization, phone access, wallet activation or provisioning change. Full support is still unfinished.

