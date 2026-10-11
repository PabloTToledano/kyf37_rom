# All-app port continuation — 2026-10-09

Owner: continue until all apps are ported. **Unfinished. Offline-only instruction
remains active.** No phone activity was performed in this continuation. Do not
translate candidate assembly/signature checks into a hardware-ready claim.

Read `kyf37-rom/all-stock-app-ports/README.md` and `readiness.md` first. Inventory
accounts for 158 stock APKs and all 55 Kyocera packages. Six existing selected
ports are preserved; MobileLight remains replaced by Kyf37Flashlight. Reconstructed
48 additional Kyocera candidates plus five FeliCa/payment companions (53 APKs).
No optional candidate was added to PRODUCT_PACKAGES or the system-image app tree.
Package-only locked build plus services passed; APKs are platform-signed. Android
APK verifier checks API29 and expected platform public certificate.

47/53 candidates have no unresolved directly invoked boot-class API contracts.
All 53 have zero missing named framework-resource references in the app audit.
Four bundled JNI libraries resolve strong symbol names/dependency names. One app
(MobileFeliCaSettingApp) has five optional OpenMobileAPI class references missing
from the stock extraction as well. This is not a fake success implementation.
All candidates still require runtime/provider/reflection/JNI/keypad/permissions
verification. Current hardware-readiness count for the new candidates is zero.

Main source scripts: inventory/port/audit/build/report scripts with names under
`device-inspection/` listed in the candidate README. New adapters are
`kyocera-port/Kyf37StockAppCompat.java`; binary manifest migration adds required
Android10 service permissions only to apps using those adapters. Native bridge
recognizes exact package assets; native key policy includes only app DEXs referencing
the guide API. Generic footer/Home clock policy remains in force. Policy scripts
now write only changed contents, avoiding repeated services recompilation.

32 original OEM resources were recovered (37 configurations), including five
nine-patches with preserved pixels/stretch/padding. Stock XML numeric enums/flags,
layout dimensions and theme attribute IDs needed source conversion; first two
framework-resource attempts failed, third passed. Named overlay staging is
`fix-android10-remaining-stock-resources.py`, automatically called on future
systemimage/framework-res builds. Regenerate candidate APKs after framework ID
changes. Extraction uses a Windows venv because WSL Python lacks ensurepip; pinned
dependency versions are saved. WSL connection timeouts occurred during the broad
14m14s framework/services build, but the build completed and final artifacts were
collected. No WSL/device reset was performed.

Later permission migration rebuild initially failed before compilation: the
shared `tv-oem.mk` final copy pair ended in a backslash immediately before
PRODUCT_PACKAGES. `fix-android10-product-continuations.py` repairs only this exact
separator pattern, preserving copy pairs and packages, and is called before
lunch. It does not rewrite other agents' generators. Final locked rebuild passed
in 56 seconds; all 53 signatures, current source payloads and adapter permission
declarations were then verified. The candidate image-staging count is zero.

Remaining concrete work:

1. AfpHome/lifesettings manner-mode/default streams and Readout separate speaker
   routing. OEM streams10–14 have different Android10 meanings. Do not use global
   speakerphone/music as a substitute. Dialer uplink/answering-machine audio is
   another existing blocker.
2. Ecomode NumberPicker full numeric-entry/automatic-focus behavior: original
   vendor smali is `vendor-framework-smali/android/widget/NumberPicker.smali`.
   onNextFocus is called after completing a number and from dispatchKeyEvent;
   generic D-pad-arrow callbacks do not reproduce it.
3. InfoServer package size/network cycles/old MediaContainer. Original
   DefaultContainerService absent from product; its recovered reference smali
   is `remaining-stock-ports/reference-container-smali`. getFileSystemStats
   returns `[f_blocks*f_bsize, f_bavail*f_bsize]` and throws on statvfs failure.
   Caller-only method adapters would leave the old service binding broken.
4. IrDATransfer custom-vCard/profile provider, shared UART with FeliCa.
5. FeliCa service/driver/SELinux/permissions/trust/chip transactions; optional
   OpenMobileAPI availability; payment trust/provisioning. No NFC-reader/payment
   support claim. NextFP shared library has exact package-manager declaration
   and optional dependencies for EmgBuzzApp/Edy; not activated live.
6. Stock sysupdater must use owner-ROM release/rollback flow before activation;
   old OTA/setup/MDM/carrier services remain optional and unenabled. Endpoint and
   certificate behavior may prevent original carrier services functioning.
7. Existing stock dialer/cellular/One Seg TV blockers remain in their own docs.

Do not copy isolated framework-res/services/framework JARs onto the phone. A
future full ROM needs matching framework/ART assets and existing validated
owner-signed pipeline; preserve current default dialer and stock rollback.

## Offline adapter continuation (later owner instruction)
Owner explicitly requested all-app port work offline. Prior launcher attempt failed after backup when the phone disconnected; do not report installation success or retry while offline. InfoServer real package storage statistics and monthly cycle adapters added; IrDATransfer profile lookup reproduces original profile-creation contract. 14 cycle tests and 11 compiled Android reflection-contract checks passed; all 53 signed candidates rebuilt. See kyf37-rom/all-stock-app-ports/OFFLINE-ADAPTERS-20261009.md. MediaContainer, custom vCard, audio streams/routing, Ecomode numeric focus, FeliCa/payment, stock OTA/dialer/TV blockers remain. Current default and PRODUCT_PACKAGES unchanged.

