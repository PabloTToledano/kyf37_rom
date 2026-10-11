# KYF37 keypad IR remote — offline experimental implementation

This is a real protocol encoder and GPIO transmitter implementation, not a mock
remote. **It has not yet controlled a physical TV or AC.** Installing the APK
alone on the current ROM does not add the GPIO kernel backend. No ADB or phone
operations were performed for this work. No release boot/system image was changed.

## Hardware evidence and remaining uncertainty

The OEM kernel maps infrared UART TX to GPIO 20, RX to GPIO 21, shutdown to GPIO
22. `irdadaemon` opens `/dev/ttyHSL3` and `/dev/irdasd`. The UART's IrDA conversion
is switched by ioctls 0x5470/0x5471. Device-tree pinctrl already exposes GPIO and
UART functions for TX. Thus software can attempt direct timed transmitter-input
pulses by switching GPIO 20 to GPIO output during a frame. All six **actual boot
QCDT entries** were parsed: `uart3_inactive` already sets TX20 to function 0,
and `uart3_active` sets it to UART function 3. The final backend reuses those
states and does not require any changes to the OEM `dt.img`. See
`stock-qcdt-ir-audit.json`. Whether the fitted
optical transceiver reproduces those pulses usefully for consumer IR is still
unknown: neither its component identity nor an optical waveform was measured.

Kyocera's catalogue says remote control is unsupported in stock firmware. That
does not by itself rule out this kernel experiment:
https://www.kyocera.co.jp/prdct/telecom/consumer/support/assets/kyf37_catalog.pdf

## App

Package `org.kyf37.remote`, launcher label **IR Remote**. Works without a network;
no INTERNET, location or storage permissions, accounts, ads or boot services.
The document picker reads one selected JSON file and saves it inside the app.

- D-pad: select, using the ROM's shared focus theme (blue fallback on older ROMs);
  OK: activate. No touchscreen is required.
- Digits 1–9: first nine visible actions. 0: profiles. Back: profiles/exit.
- `*`: transmitter check. `#`: pulse mode settings.
- TV: power, volume, channel, mute, input. Held keys do not send repeated toggles.
- Gree AC: explicit ON/OFF, 16–30°C, auto/cool/dry/fan/heat, fan 0–3, swing.
  Temperature/mode/fan/swing changes update the requested state; **8 sends it**.
  Auto mode sends 25°C; dry mode sends fan 1. Requested state is not confirmation
  that the appliance received it. Two Gree profiles distinguish YAW1F/YBOFB power.
- Imported commands can cover other TV/AC models using complete raw frames.
  This is not universal brand/model coverage or IR learning.

The app first uses Android ConsumerIrManager if a real consumer emitter exists.
On KYF37 it otherwise requests Magisk root to execute its embedded ARM32 helper.
Root approval and the custom kernel are required for that path. Target SDK 28
allows the app-private helper to execute on Android 10. App source, helper and
kernel sources are included next to the APK for review/rebuilding.

## Protocols and evidence

TV presets: Samsung32 address 0x0707, LG NEC address 0x04, Sony SIRC-12 address 1.
They are common code sets, not a promise that every branded TV uses those codes.
Sony sends three complete frames 45ms apart; NEC/Samsung send one complete frame.
Gree sends both state blocks with the separator and checksum.

Protocol references, used for independent encoders and known-vector checks:

- https://github.com/Arduino-IRremote/Arduino-IRremote
- https://github.com/crankyoldgit/IRremoteESP8266/blob/master/src/ir_Gree.cpp
- https://github.com/crankyoldgit/IRremoteESP8266/blob/master/src/ir_Gree.h
- https://github.com/crankyoldgit/IRremoteESP8266/blob/master/src/ir_Kelvinator.cpp
- https://github.com/crankyoldgit/IRremoteESP8266/blob/master/test/ir_Gree_test.cpp

No downloaded library binaries are included. Local source code is available;
the new native helper and kernel extension are GPL-2.0-only.

## Import format

One profile, 1–80 named commands, maximum file size 500KB. JSON numbers are decimal:

```json
{"name":"LG TV","commands":[
 {"name":"Power","protocol":"nec","address":4,"command":8},
 {"name":"Volume +","protocol":"nec","address":4,"command":2}
]}
```

Other protocol values: `samsung` (16-bit address) and `sony12` (5-bit address).
For any AC/other remote using raw frames, use `protocol: "raw"`, `frequency:
38000`, and `timings: [...]`: alternating mark/space durations in microseconds,
starting with a mark. Include the complete device-specific frame/checksum and
any necessary repeats/gaps. No fabricated universal AC command is supplied.
Up to 1024 durations, each space ≤100ms, each mark ≤10ms, whole waveform ≤400ms.

## GPIO kernel backend

`fix-android10-ir-remote-kernel.py` stages an idempotent kernel extension;
no boot/kernel is installed or staged into the ROM product. The new ioctl
is restricted to CAP_SYS_RAWIO and UART physical base 0x078b0000. Input bounds
are checked before mux changes. GPIO numbering is resolved from the registered
`msm_tlmm_gpio` chip's base, rather than assuming Linux's GPIO base is zero.
Carrier range 30–60kHz, normal 1/3-duty pulses or
experimental narrow 2µs pulses, with optional inversion. Inversion is an experiment,
not a verified electrical requirement. Driver restores UART pinctrl afterward.

The helper obtains the existing kflcd UART exclusion using 0x11 (status 2),
holds an exclusive process lock, opens the original shutdown gate, transmits one
bounded frame, closes the gate, switches IrDA conversion off, releases UART with
0x12. Missing arbitration/kernel support produces an error and no frame. It does
not stop FeliCa/IrDA services or steal a busy UART. SIGTERM/SIGINT request cleanup;
SIGKILL/process death cannot execute the kflcd release exchange (the gate fd still
closes automatically). This needs a recovery check before deployment.

Software carrier generation keeps interrupts enabled and disables preemption
only during each ≤10ms mark. Carrier-edge lateness >8µs or space lateness >200µs
aborts with ETIME instead of claiming success. Optical timing/range and reliability
under Android load still need measurement. A hardware-timed transmitter may be
required if this direct-GPIO method fails timing or transceiver checks.

## Offline verification result — 2026-10-09

- App Java/D8 compilation, APK packaging/alignment and signatures v1/v2/v3 pass.
- Native ARM32 PIE helper is compiled; host build passes `-Wall -Wextra -Werror`.
- GCC 4.8 compiles the final modified UART kernel object successfully.
- All six actual stock QCDT entries validate existing GPIO/UART pin states; a
  representative MSM8909 source DTS also compiles. Original `dt.img` is unchanged.
- Known NEC/Samsung/Sony/Gree vectors, 600 AC-state combinations, malformed
  native input rejection and 4108-byte ioctl ABI checks pass.
- The first locked native build finished with BUILD_EXIT=0. A later locked
  confirmation reached successful/up-to-date native targets but the shared
  wrapper returned 127 afterward (`-android10-remaining-stock-resources.py:
  command not found`). That wrapper result is not reported as a clean success.
  Standalone final APK build and signature verification subsequently passed.
- Initial toolchain launcher failures were corrected by using the existing
  compiled ARM helper and invoking D8/apksigner Java entry points directly.

No full kernel image, matching out-of-tree module set or new ROM ZIP was built
for this feature. No claim of live keypad behavior, optical output or device
control. The current phone remains unchanged by this task.

## Reproduce offline

Run scripts in WSL from this workspace:

1. `python3 device-inspection/fix-android10-ir-remote.py`
2. `bash device-inspection/build-locked.sh ~/ir-remote-native-build.log kyf37_ir_tx`
3. `python3 device-inspection/build-ir-remote-offline.py`
4. `python3 device-inspection/test-ir-remote-offline.py`
5. Kernel source: `python3 device-inspection/fix-android10-ir-remote-kernel.py`.
6. DTS check: `python3 device-inspection/check-ir-remote-dts.py`.

The normal ROM package remains unchanged. `--include-rom` is an explicit option
on the app staging script; use only after hardware validation. For an AOSP APK
build, run staging with `--embed-helper` after building the helper, then build
`Kyf37Remote` through build-locked.sh. The standalone builder includes the helper
without modifying shared APK build outputs and signs with the existing platform
key (never the owner's protected boot-signing key).

Before any kernel deployment: normal locked kernel build, rebuild wlan/core_ctl
for the same kernel, image/module/vendor gates, matching validated release image,
owner-signed boot and stock rollback retained. Follow AGENT-BRIEFING.md and
flash-release.ps1. **Do not flash an isolated object or unsigned kernel.**

## Hardware acceptance still needed

Confirm pin polarity and optical carrier/duty with an IR receiver/oscilloscope,
check original IrDA/FeliCa ownership recovers on success/failure/cancellation,
measure timing under Android load, then test explicit power/volume on a known TV
and ON/OFF/temperature on a compatible AC. Verify keypad, Back/lid behavior and
no transmission after leaving the app. No physical-device control is claimed yet.

## 2026-10-10 live integration (later status supersedes offline notes)

Phone v19/kernel #17: APK installed, root broker active from /data/local/tmp,
external GPL module loaded without a boot/partition flash. Module and the pulled
live core_ctl module match current Module.symvers with zero CRC mismatches.
No su exists on this phone; app now uses a root/system-only Unix socket and is
platform-signed with system shared UID. There is no network permission.

The stock kflcd service hangs in felicadev_open or CEN retry and cannot answer its
socket. Helper first attempts normal arbitration; on failure it stops kflcd,
waits for stopped, scans all /proc/*/fd for /dev/felica or /dev/ttyHSL3 owners,
then reserves /dev/felica_ue. Any owner or uninspectable process blocks output.
Release closes UART/IR gate, clears reservation and restarts kflcd. This restores
its service state; it does not fix the already broken NFC stack.

Initial tests rejected IRQ-delayed carrier edges and an usleep-delayed header
space (~1.4 ms late). Current driver masks IRQs only inside each bounded mark
(maximum 10 ms), enables them in spaces, uses a deadline loop for short spaces
and sleeps early in long spaces. A full Samsung volume frame from app keypad
passed: 38 kHz, 67 durations, sent=1 failed=0, no timing failure. This confirms
software/driver completion, not measured optical frequency or TV response.
User has been asked to aim at their Samsung TV and press 2; reply pending.

Keypad app UI dump: live-ui.xml. Digits 1 opens Samsung; within Samsung 1=power,
2=volume+, 3=volume-, 4/5=channel+/-, 6=mute, 7=input, 0=profiles. D-pad/OK
works through real Button focus; *=probe, #=pulse polarity/duty settings.

Persistence installer tools/install-ir-remote.ps1 is prepared but not applied:
first attempt failed before remount because WP helper lacked execute permission;
installer now fixes mode. Retried installer waits for systemui-loop phone lock.
/system remained read-only, no boot/recovery/partition image modified. Runtime
module/broker will disappear after reboot unless persistence install completes.
Startup script deliberately refuses kernels other than exact #17: rebuild and
ABI-check the external module before any later kernel deployment. Do not blindly
include this module in future ROMs. Reboot and actual TV/AC control remain unverified.

Final build addendum: normal arbitration status 1 (busy) now blocks output; direct
handover is allowed only if the daemon is unavailable, not when it reports busy.
Native final locked build and APK signing passed; final artifacts are ready but
this small helper guard is not yet live due to the SystemUI lock. Waiting
installer was cancelled explicitly so it cannot perform an unattended install.
No installer process remains. Run tools/install-ir-remote.ps1 when the phone is
free, then verify reboot startup and physical Samsung response. Later /system RW
observation belongs to the active systemui-loop session; IR did not remount it.

## Connection reset corrected — 2026-10-10
The queued persistence installer had pushed helper/service into /data/local/tmp
before failing on the WP helper. ADB push reset file mode to 0666. The running
broker remained alive but exec of the transmitter failed (127), causing the app
connection reset. Restored both executable modes to 0700 on device. A forwarded
probe received the complete expected backend-available reply after this fix.
No waveform was sent during the connection repair. Installer now chmods staged
executables immediately after push; broker source logs execl failure explicitly.
Final installer/persistence and physical TV response remain pending.
