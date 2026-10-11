# MODEM-RIL-FIX-20261011: Android now gets the SIM status (PIN prompt, emergency-only service)

## Root cause (measured with qcril debug logging, `persist.radio.adb_log_on 1`)
1. **The radio state was never UNAVAILABLE after power-on.** Earlier notes misread RILJ's log: RILJ prints `TelephonyManager` values
   (0=OFF, 1=ON, 2=UNAVAILABLE), not HAL values. Real sequence: qcril `currentState() -> Radio Unavailable(1)` at start (RILJ "2"),
   later `currentState() -> Radio On(10)` (RILJ "1"). qcril's state values map 1:1 to Android 10 (OFF 0 / UNAVAILABLE 1 / ON 10), so no
   state conversion is needed. Hypothesis "old qcril state enum mapped to UNAVAILABLE" is refuted.
2. **The first GET_SIM_STATUS fails legitimately** (card still UNKNOWN: qcril answers Generic Failure). qcril then sends
   `RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED` (card Not ready -> PIN), RILJ re-queries and qcril answers `Success, Len 284`.
3. **The 284-byte answer was rejected** by Android 10 libril (`responseLen != sizeof(RIL_CardStatus_v6)` = 280): `getIccCardStatusResponse: Invalid response`
   -> INVALID_RESPONSE -> UiccController never created a card. The 4 extra bytes are a **seventh header word**, not at the end:
   qcril layout = `[card_state][universal_pin_state][extra][gsm_idx][cdma_idx][ims_idx][num_apps]` + 8 x RIL_AppStatus (32 B) = 284.
   Observed header: `1,0,0,0,-1,-1,2` then app0 = USIM, APPSTATE_PIN. (The earlier "accept len >= 280" build read the header shifted by one word:
   n=-1 -> rejected anyway.)

## Fix
`device-inspection/fix-android10-ril-cardstatus.py` (idempotent, chained in `build-kyf37-android10.sh` nav loop as `ril-cardstatus`):
in `radio::getIccCardStatusResponse` a 284-byte response is converted into a local `RIL_CardStatus_v6` (gsm=w3, cdma=w4, ims=w5, num=w6,
apps copied from byte 28), and `num_applications` is range-checked. `KYF37_RIL_MODE=diag` adds a hex dump (never ship). Built with `m libril` (65 s).
Installed live: `/system/vendor/lib/libril.so` md5 `8c60e420087125ee8ba8f873db44f4df` (artifact `radio-work/ril-patch/libril.convert.so`).

## Verified on the phone (v19, kernel #17), including after a full reboot with qcril logging OFF
- `gsm.sim.state=PIN_REQUIRED`; RILJ `GET_SIM_STATUS IccCardState {CARDSTATE_PRESENT, num_apps=2, gsm_id=0 {APPTYPE_USIM, APPSTATE_PIN, pin1=ENABLED_NOT_VERIFIED}}`;
  UiccCard/UiccApp created, `LOCKED` notified.
- `dumpsys isub`: subscription id 1 (iccId 8934072700091159988, slot 0), carrier name "Emergency calls only".
- `dumpsys telephony.registry`: `mIsEmergencyOnly=true` (voice reg state OUT_OF_SERVICE + emergency flag = limited service, no longer POWER_OFF).
- Lock screen screenshot (`radio-work/ril-patch/screen1.png`): "Enter SIM PIN." keypad, "... CALLS ONLY (SIM CARD IS LOCKED.)", EMERGENCY. **No PIN was entered or tried.**
- No `Invalid response` for GET_SIM_STATUS in the post-reboot log.

## Not done / remaining gaps
- (c) Registration after the owner enters the PIN is **not verified** (needs the owner). Modem camps on GSM 214-03 weakly (rssi -79 reported); success depends on RF.
- `RIL_REQUEST_START_LCE` still returns INVALID_RESPONSE (`responseInt: Invalid response`; old qcril reply length differs from sizeof(int)); harmless for telephony.
- IRadio 1.4 vs libril V1_1 manifest warnings and absent IRadioConfig were not needed for the SIM state; left unchanged.
- qcril "AutoinputPIN1" logic (`Don't get PIN1 or Not Set`) is Kyocera's stored-PIN feature; untouched.
- `QMI_PORT_NOT_OPEN` for conn 29/48/57 (netmgrd data ports) unexplained; affects mobile data only.
- Fix is in the source tree/build script but only the live phone has it until the next ROM build.

## Rollback
`adb root; adb push device-inspection/clear-system-temp-wp /data/local/tmp/; adb shell /data/local/tmp/clear-system-temp-wp --clear-system-temporary; adb shell mount -o remount,rw /system;
adb push radio-work/ril-patch/libril.orig.so /system/vendor/lib/libril.so; sync; mount -o remount,ro /system; reboot` (orig md5 438629c1..., also `/data/local/tmp/libril.orig.so`).
