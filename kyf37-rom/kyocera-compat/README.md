# Kyocera launcher compatibility work

First port: app-local KCfpSoftkeyGuide implementing the seven method signatures
used by the deoptimized AfpHome launcher. It draws five labels in a bottom bar,
supports independent enabled states, show/hide and resource/string labels, and
reserves content space. It uses standard Android APIs instead of stock Kyocera
Window extensions. No touch input is needed to display the guide.

Compiled with JDK 8 against the existing Android 7 SDK classes, converted to DEX,
and assembled together with the previously patched original launcher smali as
AfpHome-softkey-port.dex. Reproduce with device-inspection/build-kyocera-softkey-port.sh.

This is an offline partial port, not an installed or runtime-verified launcher.
Dialog F1/F2/F3 button assignment, list wrapping/paging and Activity-based overflow
button hiding now have app-local implementations. A window callback wrapper
preserves existing View/Dialog key listeners. An unsigned APK preserves 223
original manifest/resource files byte-for-byte and embeds the adapted DEX.
Label ordering, clipping,
multi-child window layouts, automatic label tokens and lifecycle behavior need
review and runtime testing. Stock appearance is not yet reproduced. The helper
also compiles successfully against the official API 29 public android.jar from
android-10.0.0_r47. Neither compilation verifies Android 10 launcher behavior,
and the helper has not been tested on a phone.
App resources, manifests, privileges/signatures and framework dependencies must
be checked before packaging and installation.

Static audit of the merged DEX checks 1,213 Android framework method references:
zero unresolved framework, external Kyocera helper or owned-class methods against
the existing Android 7 framework/SDK. This checks method
references only; fields, reflection, resource inflation and behavior are not
validated by that result. See ../afphome-softkey-port-api.json.

An aligned binary scan finds 117 stock framework resource IDs in the staged APK,
all matching the actual Android 7 framework by name and ID. It can include false
positives and does not prove every resource compatible.

Android 10's public-SDK audit flags nine methods. All nine are retained in pinned
Android 10 platform source (Canvas, SystemProperties, QuickContact, FloatMath,
Pools and Window). Hidden-API access policy and runtime semantics remain untested.

Conditional F3/F4 policy sources are staged under policy-source. Both modified
Java sources compile against existing Android 7 build classes. They have not
been applied to the build tree or packaged into a ROM. The proposed policy lets
F3/F4 reach the unlocked original launcher, retains F3 Home/F4 cursor elsewhere,
and maps physical scan code 61 back to F3. Complete policy/DEX/keyguard/wake and
physical press/release/repeat checks remain required.

Remaining integration work includes the original notification, Telecom and
info-sign provider contracts, signing with the ROM's platform certificate,
privilege checks and actual launcher startup/physical-key tests. The existing
flashed Android 7 ROM's first boot remains unverified. No phone state was changed
during this offline work.
