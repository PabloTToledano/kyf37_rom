# KYF37 custom ROM candidate — pending integration and runtime validation

Base: LineageOS 14.1, Android 7.1.2, ARM 32-bit Cortex-A7. This advances the
stock Android 5.1.1 software while keeping the OEM Linux 3.10 kernel and
hardware drivers. The phone has approximately 1 GB RAM; this candidate uses
low-RAM settings and a compact system selection. Android 8.1/Go is a separate
unflashed candidate, not the base of this image.

Physical controls: keypad launcher, multitap keyboard, D-pad focus, and F4
cursor mode for apps requiring pointer input. F3 maps to Home. Cursor mode
supports D-pad movement and center-key click/hold/drag. These components
compile; their behavior on the new ROM still requires verification.

Outer screen: OEM framebuffer driver with a new 128x72 monochrome clock and
battery service, controlled by the lid state. Packaged Java components and
JNI declaration are verified. Actual display output and suspend behavior
are not yet verified. Caller and notification previews are not implemented.

Sound: original OEM UI recordings, opening/closing playback, and physical
button clicks. Source compilation passed; policy integration is applied and
a build is running. Recording priority is corrected; all 28 installed OEM UI
recordings match the stock files byte-for-byte. Compiled feedback policy calls
are verified. Actual playback is still untested.
Explicit saved OEM sound settings are honored; absent settings
default enabled. Original per-window key suppression flags remain pending.

Stock application preservation: Kyocera framework resources are included;
original launcher port is incomplete and no original flipphone application
suite has been packaged as a verified working replacement. Keypad navigation
provides the requested fallback, subject to actual ROM runtime tests.

Recovery: retain the separately maintained owner-signed keypad TWRP. Build
configuration disables generated recovery replacement payloads. Modem,
calibration, and owner keystore partitions are outside the ROM flash scope.

Before any flash: finish integration/build, verify final image content and
partition fit, sign the boot image with the enrolled owner key, verify the
recovery/rollback artifacts, and print an updated summary to the user.
The initial boot is a bring-up test: boot, telephony, audio, Wi-Fi, physical
keys, lid, outer display, and app compatibility are currently unproven.

System and owner-signed boot have now been flashed. Full partition readback
hashes matched the verified candidate; recovery and keystore hashes stayed
unchanged. The first boot has been requested, but Android startup and USB
connectivity are not yet verified. See flash-readback-verification.json.

Fresh read-only pre-ROM backups of boot, recovery and keystore are saved in
`phone-backup/pre-rom-20261007`. Their exact bytes and hashes match the known
working owner-signed boot, keypad TWRP, and enrolled owner keystore. The local
signing keystore also matches the freshly read device keystore.

Root retention: existing Magisk runtime data is present. A ROM-specific
startup helper preserves the new xbin tools and avoids the absent stock
dexdump dependency. Its syntax passed both host and phone shell checks;
both scripts are verified inside the final filesystem image. App-root
operation on the new ROM remains untested.
