# Japanese One Seg TV (KYF37) — ROM integration

Investigation and prepared artifacts: `modem-investigation/tv-tuner/README.md` (read it first). Integration into the ROM source tree is done by
`device-inspection/install-tv-oneseg.py` (idempotent, WSL). **Nothing was built or packaged for it yet; it ships with the next release after v15.**

## What gets installed

| Item | Where on the phone | Notes |
|---|---|---|
| `FsDtvApp` (`jp.co.fsi.fs1seg`, OEM One Seg app, unsigned reconstruction) | `/system/app/FsDtvApp` | platform-signed by the build; OEM code unchanged |
| `Kyf37Tv` launcher / support checker (`org.kyf37.tv`) | `/system/app/Kyf37Tv` | keys **1** open the OEM app, **2** check backend files/nodes, **3** explain requirements; platform-signed so it can start the daemon |
| `dtvserver` | `/system/bin/dtvserver` | on demand: init entry changed from `class main` to `disabled, oneshot`; the launcher starts it with `ctl.start` |
| 15 libraries (`libDtv*.so`, `libdtvtuner.so`, JNI at `/system/lib/libDtv_jni.so`, `libDtvBml_jni.so`) | `/system/lib/` | exact stock files (hashes in `stock-port-report.json`) |
| `media/dtv` sounds and graphics | `/system/media/dtv/` | |
| `public.libraries-kyocera.txt` | `/system/etc/` | lets the app's linker namespace load the absolute-path JNI libraries |

The libraries are intentionally **not** in `vendor/kyocera/kyf37/proprietary-files.txt`, so the installer's strict vendor-symbol audit (which must report zero
unresolved symbols) is not affected by the known gaps below.

## Known limits (honest)
* `native-compatibility-audit.json`: 62 unresolved imports (Skia, ICU 53, old `GraphicBuffer`/`AudioTrack`) in `libDtv`, `libDtvULayer`, `dtvserver`. Until a compatibility
  layer or rebuild exists the daemon will fail to start; the launcher reports that instead of pretending. Do **not** replace Android 10 system libraries with Android 5 ones.
* One Seg is ISDB-T 1seg (Japan); Spain broadcasts DVB-T. No stations are expected even with a perfect port.
* The tuner power driver powers off when its file handle closes; a future backend must hold it for the whole session. Nothing in this integration opens `/dev/dtvtuner_pm0`
  or powers the tuner; no hardware test was performed.

## Static checks
`python3 device-inspection/check-tv-integration.py` (WSL): sources exist, no duplicate destinations, all ELF files 32-bit ARM, `dtvserver` executable.
A full build of the integration was not completed because a concurrent Wi-Fi edit by the radio agent (`device.mk`, duplicate `wpa_supplicant.conf`) breaks the shared build; retry once it is fixed.
