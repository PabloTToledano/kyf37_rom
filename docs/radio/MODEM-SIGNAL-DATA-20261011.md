# MODEM-SIGNAL-DATA-20261011: signal icon flapping and mobile data (both fixed by one libril change)

## Root cause (one bug explains both problems)
`rild` was **crash-looping** (tombstones 03..22+, a new one every few seconds while Android retried the data call):
`SIGSEGV` in `strcat` <- `libril-qc-qmi-1.so qcril_data_request_setup_data_call+9864` <- libril `dispatchStrings` <- `RadioImpl::setupDataCall`.
Disassembly (`radio-work/signal/setup_all.dis`): Kyocera's Android 5.1 qcril reads `data[0..8]` of the RIL_REQUEST_SETUP_DATA_CALL string
array (`data[7]`, `data[8]` optional; at 0x4ae26c it does `if (data[8]) { if (data[7]) append 2 bytes; strcat(buf, data[8]); }`).
Android 10 libril (version<=14 path) sends only 7 strings, so `data[8]` was heap garbage (fault: r1=0x1) -> crash.
Every crash killed the HIDL radio proxy (`HwBinder Error -32`, `EVENT_RADIO_PROXY_DEAD`), rild restarted, SST polled again:
`mVoiceRegState` toggled IN_SERVICE <-> OUT_OF_SERVICE every ~3-8 s (observed in `dumpsys telephony.registry`) and the stored
SignalStrength went to "unavailable" -> status-bar icon: full bars, then none. The modem itself stayed registered (-67..-69 dBm).
There was no signal-struct mismatch: the signal path (RIL_UNSOL_SIGNAL_STRENGTH / getSignalStrength) was never at fault, so no change to it.
(Note: the reading is stored in `mWcdma ss=-69 level=4` with `primary=CellSignalStrengthWcdma` and the GSM rssi field stays unavailable;
this is stable and gives 4 bars, cosmetic only.)

## Fix
`device-inspection/fix-android10-ril-setupdata.py` (idempotent, chained as `ril-setupdata` in `build-kyf37-android10.sh` nav loop after
`ril-cardstatus`): the varargs `dispatchStrings` in `hardware/ril/libril/ril_service.cpp` now `calloc(countStrings + 2, ...)`, so qcril's
optional data[7]/data[8] are NULL; request length unchanged. Built with `build-locked.sh <log> libril` (63 s, BUILD_EXIT=0).
Installed live: `/system/vendor/lib/libril.so` md5 `cee9630c230635ecc1c5d4a9c6dfe53a` (artifact `radio-work/ril-patch/libril.setupdata.so`;
previous installed = `libril.convert.so` md5 8c60e420..., backup `libril.convert-installed.so`; stock `libril.orig.so`).

## Verified on the phone (v19, kernel #17, Movistar 214-07, SIM unlocked by the owner)
- rild stable: same PID, no new tombstone after the fix (count stayed 54); previously one every few seconds.
- 62 samples at 5 s (about 5 min): 62/62 with `mVoiceRegState=0 IN_SERVICE` and `ss=-69` valid, 0 bad. Screenshot
  `radio-work/ril-patch/signal-bars.png`: status bar shows "G" with full steady bars.
- **Mobile data works** with no further change: `dumpsys connectivity` -> MOBILE[GPRS] CONNECTED, APN `telefonica.es` (Movistar), `rmnet_data0`
  10.71.246.191/25, DNS 80.58.61.250, `NET_CAPABILITY_VALIDATED`. With Wi-Fi disabled: `ping -I rmnet_data0 8.8.8.8` 3/3 (300 ms),
  google.com 2/2, HTTP 204 from connectivitycheck.gstatic.com (3 pings + 1 HEAD only). Wi-Fi re-enabled afterwards.
- The earlier `QMI_PORT_NOT_OPEN` conn_id 29/48/57 noise was a side effect of the crash loop / harmless; DATA ports are not an issue.
  qcril logging was ON during this pass (props read 0 now: `persist.radio.adb_log_on` 0, `persist.vendor.radio.adb_log_on` 0).

## Not done / gaps
- **Full reboot not performed on purpose**: a reboot re-locks the SIM and the owner would have to re-enter the PIN (I may not type it).
  Persistence rests on the file being on /system (md5 verified after remount ro, same procedure that survived reboots before). Please confirm
  after the next reboot.
- Only the live phone has the fix until the next ROM build (source tree + build script are updated).
- Data is GPRS (2G, speed ~ tens of kbit/s); LTE/WCDMA camping not investigated (RF / band mask see MODEM-STATUS).
- VoLTE/IMS, calls and SMS not tested in this pass.

## Rollback
`adb root; adb push device-inspection/clear-system-temp-wp /data/local/tmp/; adb shell /data/local/tmp/clear-system-temp-wp --clear-system-temporary;
adb shell mount -o remount,rw /system; adb push radio-work/ril-patch/libril.convert.so /system/vendor/lib/libril.so;` then chmod 644, chcon u:object_r:vendor_file:s0,
sync, remount ro, `stop ril-daemon; start ril-daemon`.
