<div align="center">

# KYF37 ROM

### A keypad-first **Android 10 Go** (LineageOS 17.1) for the **Kyocera GRATINA KYF37** flip phone

![Android](https://img.shields.io/badge/Android-10_Go-3DDC84?logo=android&logoColor=white)
![Base](https://img.shields.io/badge/base-LineageOS_17.1-167C80)
![SoC](https://img.shields.io/badge/SoC-MSM8909_%7C_32--bit-blue)
![Kernel](https://img.shields.io/badge/kernel-3.10.49-orange)
![Status](https://img.shields.io/badge/status-experimental-yellow)
![License](https://img.shields.io/badge/license-Apache--2.0-informational)


</div>

The KYF37 shipped with Android 5.1.1, a 480×854 **non-touch** panel, a D-pad, a number pad and a tiny 128×36 outer display.
This project brings a modern Android to it **without losing the keitai experience**: everything is reachable with the keypad,
the original Kyocera apps still run, and the cover display is a real, useful screen.

> **Experimental.** This is a hobby port for one specific phone. It works day to day on the author's device, but not everything is verified
> (see [Status](#status)). You can brick your phone. Read [Safety](#safety) first.

## Highlights

| | |
|---|---|
| **Keypad navigation everywhere** | System-wide focus themes (7 palettes), D-pad-friendly Settings, setup wizard, lock screen, notification shade and quick settings, pointer mode as a fallback, *Clear* deletes text |
| **Keitai launcher** | 3-column icon grid, digits 1–9 launch tiles, **move tiles in the grid**, **folders**, icon shapes (circle, squircle, square, teardrop…), three icon themes (Standard, Pastel Star, Sky Star, Kyocera Classic) |
| **Contextual corner keys** | The four corner keys and OK are labelled on screen and change with the app (Contacts, Camera, Email, Browser) |
| **Outer screen v2** | Crisp hinted pixel fonts, clock with date and battery, **incoming-call and notification screens with scrolling text**, mascot animations, Bad Apple mode, screen timeout and settings page |
| **Original Kyocera apps** | Ported to Android 10: camera, memo, calculator, sound recorder, barcode reader, data folder and more, with a compatibility layer for the old OEM framework classes |
| **Working hardware** | Wi-Fi, Movistar (Spain) mobile data and SIM PIN, camera preview and photo capture, speaker, flashlight, SD card storage, JIT, ambient-light sensor node, Magisk (runtime daemon) |
| **Tuned for 1 GB** | Low-RAM config, zram, ART JIT, measured UI-smoothness tuning and battery-first defaults |
| **Games** | An original keypad virtual pet (feed, play, clean, lights, mini-games, wardrobe) |
| **Recovery** | A custom **TWRP with a D-pad menu** so you can flash and restore without a touchscreen |

## Download

Prebuilt files are on the [**Releases**](../../releases) page:

* `kyf37-android10-go-…-twrp-v23-keypad.zip` — the ROM installer for TWRP (with SHA-256)
* `kyf37-keitai-recovery-…img` — the D-pad TWRP recovery

> The installer verifies the phone model and serial, the partition geometry and the owner keystore before it writes anything, and it
> saves matching boot/system rollback images to the microSD. **It is built for the author's device and keystore**; for another KYF37 you
> have to rebuild and re-sign it with your own key (see below).

## Status

| Area | State |
|---|---|
| Boot, Home, Settings, lock screen, notifications | ✅ working |
| Wi-Fi | ✅ |
| Cellular (Movistar ES), SIM PIN | ✅ registration and data; LTE bands limited by the hardware (B1 + B26) |
| Camera | ✅ preview and photos; ⚠️ video untested |
| Audio | ✅ speaker path; ⚠️ not all paths listened to |
| Outer screen | ✅ clock / notifications (simulated lid); ⚠️ real incoming call untested |
| Light sensor / auto-brightness | ⚠️ sensor works, brightness curve needs a flashed build |
| GPS | ⚠️ engine starts, no fix indoors |
| Bluetooth | ⚠️ no real device address |
| VoLTE / VoWiFi | ❌ not feasible on this firmware |
| Screen tearing on the physical panel | ⚠️ known, no software cause found |

The honest, detailed list lives in [`KYF37-PROJECT.md`](KYF37-PROJECT.md) and [`docs/FIXES.md`](docs/FIXES.md).

## Repository layout

```
.
├── KYF37-PROJECT.md      current state, rules, build and flash guide  ← start here
├── AGENTS.md             short brief for AI/automation helpers
├── docs/                 documentation (see docs/README.md)
│   ├── FIXES.md          every root cause and the script that reproduces the fix
│   ├── ui/ radio/ hardware/ kernel/ recovery/ releases/ history/
│   └── img/
├── device-inspection/    all build, patch, packaging and flashing scripts + app sources
│   ├── fix-android10-*.py   idempotent patches applied to the LineageOS tree
│   ├── build-*.sh · package-*.py · sign-*.py
├── kyf37-rom/            release notes, validation reports and artifact READMEs (binaries are not in git)
├── kyf37-twrp-device/    recovery tree and tooling (signing keys are never committed)
├── tools/                PowerShell / Python helpers: phone lock, flashing, screenshots, benchmarks
└── third-party/          pointers to third-party software (nothing redistributed)
```

## How it is built

The ROM is **LineageOS 17.1 with a stack of small, re-runnable patch scripts** on top of an OEM device tree and the stock 3.10 kernel.
Nothing is edited by hand in the source tree: each change is a script in `device-inspection/` so the whole ROM can be rebuilt from scratch.

```text
WSL Ubuntu            ~/kyf37-android10   (lunch lineage_kyf37-userdebug)
build                 device-inspection/build-locked.sh <log>          → system + boot
package               device-inspection/package-release.sh vNN         → candidate + validation
sign boot             device-inspection/sign-rom-boot.py               (your own key!)
installer             device-inspection/build-twrp-android10-installer.py vNN
flash (TWRP)          tools/flash-release.ps1                          (exclusive phone lock)
```

You need: the LineageOS 17.1 source, the Kyocera kernel source (GCC 4.8 only) and **proprietary blobs extracted from your own phone**
(not included). [`KYF37-PROJECT.md`](KYF37-PROJECT.md) has the exact sequence and the long list of traps (privapp allowlists, kernel/module
ABI, write-protected `/system`, …).

## Safety

* Never write the `recovery`, `keystore`, modem, persist or NV partitions, and never wipe userdata. The installer enforces this.
* Keep a stock backup and the USB recovery runbook ([`docs/recovery/USB-RECOVERY.md`](docs/recovery/USB-RECOVERY.md)). A vendor download mode lets you
  restore the phone over USB even when it will not boot.
* Boot images must be signed with the keystore enrolled on the phone. **Do not publish or share your signing key.**
* Flash only with the ROM built for your keystore; a mismatch can leave the phone unbootable.

## Documentation

* [`KYF37-PROJECT.md`](KYF37-PROJECT.md) — current state and workflow
* [`docs/README.md`](docs/README.md) — index
* [`docs/FIXES.md`](docs/FIXES.md) — root causes and reproducing scripts
* [`docs/hardware/GPU.md`](docs/hardware/GPU.md), [`docs/radio/RADIO.md`](docs/radio/RADIO.md), [`docs/ui/KEYPAD-NAV.md`](docs/ui/KEYPAD-NAV.md) — deep dives

## Credits and licences

* The original scripts, apps and documentation in this repository are released under the **Apache License 2.0** (see [`LICENSE`](LICENSE)).
* Kernel-related changes are derived from Linux and are **GPL-2.0**; see [`NOTICE`](NOTICE).
* Built on [LineageOS](https://lineageos.org), [AOSP](https://source.android.com), [TWRP](https://twrp.me), [Magisk](https://github.com/topjohnwu/Magisk),
  [TT9](https://github.com/sspanak/tt9) and [microG](https://microg.org). Kyocera firmware, apps and blobs are Kyocera's property and are **not** distributed here.

<sub>Not affiliated with Kyocera, Google or LineageOS.</sub>
