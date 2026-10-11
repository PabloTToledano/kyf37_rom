# Complete stock-app port inventory — 2026-10-09, offline work

The owner requested continuing until all apps are ported. **This is not yet a
complete or hardware-ready port.** Earlier instruction to work without phone
access remains active. No ADB, installation, flashing, provisioning, payment,
SIM, device-node access or phone input was performed.

## Scope and evidence

`inventory.json` covers all 158 stock APKs. It identifies 55 Kyocera packages:
six already-selected ports, 48 additional candidates, and MobileLight deliberately
replaced by the working single-button keypad flashlight. The candidate collection
also includes MobileFeliCaClient, MobileFeliCaSettingApp, MobileFeliCaWebPlugin,
MobileFeliCaWebPluginBoot and Edy4FP: **53 candidate APKs**. Stock Dialer and
FsDtvApp have separate migrations and blockers; see their README and TV.md.
Android platform apps and carrier/third-party packages in the full inventory
are not all interchangeable with stock Android 5 versions. Do not replace Android
10 providers, Settings or SystemUI wholesale to increase a completion count.

`readiness.md` and `readiness.json` list per-app checks and blockers. No candidate
is labelled ready from class/API resolution alone. Native ELF checks cover symbol
names, not linker namespaces, dlopen, JNI registration, Binder/struct/ioctl ABI or
feature behavior. Reflection, provider dependencies, carrier endpoints, lifecycle,
keypad control and persistence need later tests.

## What changed

* Reconstructed APKs from original embedded/deodexed DEX, preserving package,
  provider and shared-UID contracts. Added only legacy classes absent from Android
  10; Android 10 boot classes are never replaced.
* Mapped framework resources by name. Audited original binary resource references
  and bytecode literals; recovered 32 missing OEM resource definitions in 37
  configurations. Five nine-patches retain original pixels/stretch/padding.
  Framework resource build passed after converting binary XML numeric enum/flag
  encodings to source names. Initial builds failed on those encodings; logs kept.
* Removed unused AppCompat code only when no external bytecode, class-name string,
  manifest, resource or asset references existed. Preserved any original R classes;
  no missing resource IDs were invented.
* Added narrow adapters using actual Android 10 services: SD/USB volume identity
  and state, temporary display brightness, number formatting, call state/end-call,
  credential queries with current user ID, and real Soft AP start/stop requests.
  Requests retain Android permissions; service errors are not replaced with success.
  Candidate manifests explicitly request the new service permissions where used:
  NETWORK_STACK for Soft AP, CONTROL_DISPLAY_BRIGHTNESS for temporary brightness,
  ANSWER_PHONE_CALLS/READ_PHONE_STATE for call operations and credential-query
  permission for LockPatternUtils. These are not runtime grants performed on the
  phone; future installation must verify actual permission/app-op behavior.
  Legacy Face Unlock capability is unavailable; no credential/authentication bypass.
* Emergency buzzer URI uses the four exact stock sound-file mappings, already
  present in the product. Missing sound assets are an error, not a silent substitute.
* Recovered NextFP, effect, JUnit and other small legacy Java dependencies. NextFP
  has an optional shared JAR and permissions XML with its original library name.
  Both emergency buzzer and Edy require its activation if ever selected for a ROM.
* Candidate apps carry original native softkey artwork and an exact package marker.
  The app-local bridge only attaches when an app requests its guide. Native key
  dispatch is enabled only for candidates referencing the native softkey API.
  Generic SystemUI footer stays disabled; Home clock removal stays in force.

All candidates are optional source modules. **PRODUCT_PACKAGES remains unchanged.**
Package-only Ninja targets generate signed APK intermediates without installing
53 optional apps into the system-image staging directory. `signed-apks/` and
`signed-artifacts.json` contain the resulting candidates and hashes. Source APKs
are platform-signed by the Android build, not with the owner's boot signing key.

## Unfinished work

* AfpHome/lifesettings: original manner-mode audio streams/defaults; Readout:
  separate readout speaker routing. Android 10 stream numbers differ from the OEM
  uplink/buzzer/readout streams. Mapping them to ordinary speakerphone/music would
  change behavior and may affect calls; these are still unresolved.
* Ecomode: original NumberPicker digit-entry/automatic next-focus behavior, not
  merely a method name. The original widget invokes the callback after completing
  numeric entry and on a specific key; a generic arrow-key listener is insufficient.
* InfoServer: package-size/network-cycle and old MediaContainer contracts. The
  original DefaultContainerService is absent from Android 10 and needs backend
  migration; making descriptors resolve would not restore its Binder binding.
* IrDATransfer: custom vCard/profile provider contract and shared UART ownership.
* MobileFeliCaSettingApp: optional OpenMobileAPI classes/service absent from the
  stock framework extraction too. Core FeliCa device access, service lifecycle,
  trust/provisioning and actual chip/card transactions remain unverified.
  Signed APKs alone do not establish Osaifu-Keitai, general NFC or payments.
* Stock updater must use the owner-ROM update pipeline before activation. Original
  OTA/setup/MDM/payment/service apps are not auto-enabled. Carrier server, signatures
  and certificate checks may prevent original services functioning on the new ROM.
* Stock dialer answering-machine/uplink audio, cellular stack and One Seg TV remain
  separate existing blockers. Keep the current default dialer.

## Reproduction

Use the existing owner stock backups, deodexed stages, compat stages, SDK7 compile
jar, JDK8, smali tools and a built Android 10 framework-res. Run WSL scripts from
this workspace, in this order:

1. `inventory-stock-app-ports.py`; `extract-stock-shared-app-libraries.py`.
2. `fix-android10-native-softkeys.py --compat-only`.
3. `port-remaining-stock-apps-android10.py` (first audit exposes absent resources).
4. Windows `tools/stock-resource-venv/Scripts/python.exe
   device-inspection/extract-remaining-stock-resources.py`, then WSL
   `fix-android10-remaining-stock-resources.py`.
5. `build-locked.sh ~/remaining-stock-resources-build.log framework-res`.
6. Re-run `port-remaining-stock-apps-android10.py` against those actual resource IDs.
7. `audit-remaining-stock-apis.py`, `audit-remaining-stock-native.py`,
   `audit-stock-shared-library-contracts.py`.
8. `build-remaining-stock-candidates.py` (locked package-only build + services).
9. `verify-remaining-stock-signatures.py`; `report-all-stock-port-status.py`.

The resource extraction venv is local tooling only; pinned dependencies are in
`resource-tool-requirements.txt` (androguard 4.1.3, Pillow, lxml and dependencies,
installed through PyPI). WSL's current Python lacked ensurepip; those unsuccessful
venv attempts performed no phone/system changes. No new tool was run on the phone.

Future systemimage/framework-res builds automatically reapply named OEM resource
additions. Existing selected-native-app bridge and final UI policy remain in the
build wrapper. Optional candidate reconstruction must run again after framework
resource IDs change. Do not independently install framework-res/services/framework
JARs; release these only with a validated matching full ROM/ART image set.

Native key/footer policy scripts now avoid writing unchanged source files. This
keeps their policy persistent without forcing a framework/services rebuild on
every optional-app build. Signature verification uses an isolated host build of
the existing Android `tools/apksig` source, checks API 29 and matches the expected
platform public certificate. Java JAR-stream-order warnings from the preliminary
jarsigner experiment are not Android APK verification failures; the Android APK
verifier is the recorded final check.

Final validation: locked build including services passed; all 53 APK signatures,
source payloads and modern adapter permission declarations passed. Candidate
APKs total 43,841,861 bytes (about 42 MiB). Zero optional candidate APKs were
installed into the image staging tree. The final incremental build took 56s;
the earlier framework/services rebuild took 14m14s. A later shared TV product
file had a trailing copy-list backslash swallowing PRODUCT_PACKAGES; the exact
separator was repaired by `fix-android10-product-continuations.py`, now invoked
before lunch, without removing copy pairs/packages or editing its generator.
Readiness remains 47 direct-API-clear / 53 resource-clear / 0 hardware-ready.

## Live continuation — 2026-10-11
The later owner request authorizes phone testing. See LIVE-20261011.md for installed apps, real successes, failed experiments and remaining blockers. Earlier offline-only instructions/status describe the original candidate assembly. Candidates remain optional; partial tests do not establish all-app hardware readiness.

