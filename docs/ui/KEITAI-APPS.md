# Keitai Phone / Messages / Contacts apps (2026-10-10)

Replacement default apps, fully keypad driven, same look as Home / Phone settings (header strip with title + clock,
numbered rows, theme-colour selection from `Kyf37FocusTheme`, one-row soft-key hint footer, Standard/Pastel/Sky header
colour). Plain framework Java, no libraries. Cellular is still down (`MODEM-STATUS-20261009.md`), so everything that needs a
radio is built but unexecuted; everything else was walked on the phone (v19) with `tools/test-keitai-apps.ps1`.

| App | Package | Source | APK |
|---|---|---|---|
| Phone | `org.kyf37.dialer` | `device-inspection/keitai-apps/dialer` | `kyf37-rom/keitai-apps/Kyf37Dialer.apk` |
| Messages | `org.kyf37.messages` | `.../messages` | `Kyf37Messages.apk` |
| Contacts | `org.kyf37.contacts` | `.../contacts` | `Kyf37Contacts.apk` |

Shared UI toolkit: `keitai-apps/common/KUi.java` (copied into each package with `@PKG@` replaced), role migration
`keitai-apps/role/RoleBoot.java`, focus bridge `Kyf37FocusCompat.java.txt`.

## Reproduce
* `wsl -d Ubuntu -- python3 /mnt/c/.../device-inspection/fix-android10-keitai-apps.py` (idempotent; chained into `build-kyf37-android10.sh`).
  Stages the three apps into `packages/apps/Kyf37{Dialer,Messages,Contacts}`, `PRODUCT_PACKAGES`, overlays
  (`config_defaultDialer`, `config_defaultSms`, `default_sms_application`; Telecomm/Telephony `dialer_default_class`, `ui_default_package`),
  Home (hides stock Lineage tiles, pins the Messages and Contacts tiles to our packages, icon map entries).
* Build only the apps: `build-locked.sh <log> Kyf37Dialer Kyf37Messages Kyf37Contacts Kyf37Home` (about 1 min). Quick type check
  without AOSP: `keitai-apps/javac-check.sh <app>`; host tests: `keitai-apps/tests/run-host-tests.sh` (MMS PDU codec, vCard).
* Live test: `tools/test-keitai-apps.ps1 -Action all` under the phone lock.

## Design decisions
* Not priv-apps, platform-signed `/system/app`: no privapp allowlist (AGENTS.md section 4 crash loop avoided). They declare
  `CALL_PRIVILEGED` (signature) so emergency numbers placed with `TelecomManager.placeCall` go as CALL_EMERGENCY.
* Stock Lineage Dialer/Messaging/Contacts stay installed but are not default. Defaults: overlay (clean installs) plus `RoleBoot`
  (once per build fingerprint, `RoleManager.addRoleHolderAsUser`, needed because RoleManager keeps old holders on data-preserving
  updates; the phone had `com.android.dialer`/`com.android.messaging` as holders). Intent filters carry priority 100
  (effective for /system apps; with /data installs priorities are zeroed, so Home addresses our packages explicitly).
* Telecom plays the ringtone and writes the call log; the dialer only reads the log. Lockscreen "Emergency call" uses the
  platform `com.android.phone/.EmergencyDialer` (unchanged, not keypad-tested by us).
* Contacts list: digits are letter jumps (multitap 2=ABC...), so rows are not digit-numbered there; Contact view, Recents, Speed dial,
  Messages list and all menus are digit-numbered. Groups not implemented.
* MMS: receive notification (WAP_PUSH_DELIVER) -> record -> platform download -> own WSP parser stores text and parts (attachments
  are stored, not shown). Send is text-only MMS (menu "Send as MMS"); normal sending is SMS (multipart handled by SmsManager).

## Keys
| Screen | Keys |
|---|---|
| Dial pad | digits/`*`/`#` type; hold 0 = `+`; hold 1 = voicemail; hold 2-9 (empty) = speed dial; Call dials (empty: recalls last number, second press dials; after Up/Down dials the picked row); OK dials the highlighted row; Clear = backspace, empty = leave; F1 menu (Recents, Contacts, Speed dial, Voicemail, Save, Send message, Clear) |
| Recents | Left/Right filter All / Missed / Dialed / Received / Frequent; digit 1-9 jumps and opens actions; OK actions; Call dials |
| In call (ringing) | Call or OK answer; End or Clear reject; F1 reject + canned text; call waiting shows "Waiting" line |
| In call (active) | digits send DTMF; OK mute; Up speaker; Down hold; Call swaps with held call / adds call; F1 menu (hold, add, swap, merge, Bluetooth, hang up); End hangs up; Clear sends the screen to background |
| Contacts | OK open; Call dials primary; Left/Right All/Favourites; digits jump letters; F1 menu (new, search, favourites, delete, import/export vCard) |
| Contact view | numbered rows: Call / Message per number, e-mail, Edit, Favourite, save vCard, Delete (two confirmations) |
| Contact edit | Up/Down fields, TT9 types, Clear deletes (framework rule), F1 or Save row stores; Clear on unchanged form leaves, changed form asks |
| Messages | digits open conversation n; OK open; F1 menu (new, delete, mark read, settings); Call calls |
| Thread | Up/Down messages, OK = actions (resend, reply, forward, copy, call sender, delete, details); Down past the last message = text box, Down again = Send, OK sends; F1 menu (send, MMS, quick text, call, save number) |

## Verified on hardware (phone v19, apps installed with `adb install -r -d`, screenshots in `kyf37-rom/keitai-apps/iter2` and `iter3`)
* Roles taken (`cmd role add-role-holder`), Telecom binds `KeitaiInCallService` as default dialer.
* Dial pad typing, contact matching, backspace, menus; Recents tabs, actions; Speed dial; every Contacts screen; contact create via TT9
  (provider row verified), vCard import from `/sdcard/Download`; Messages list/thread rendering, received texts through the debug hook
  (provider + notification), send through `SmsManager` ends as "Failed - OK to retry" without radio (expected).
* In-call UI through the debug test line (`TestConnectionService`, needs `telecom set-phone-account-enabled org.kyf37.dialer/org.kyf37.dialer.TestConnectionService kyf37-test-line 0`):
  incoming screen, answer with Call, call timer, DTMF digit, mute with OK, menu, call waiting second incoming, remote hang-up, outgoing.
* Settings > Appearance recolours header (Standard/Pastel/Sky) live. Home shows our Phone/Messages/Contacts tiles with the Pastel icons.
* `RoleBoot` receiver triggered by hand; fresh-boot behaviour not observed.

## Built only (not executed)
Real calls, call log written by Telecom, emergency dialing, real SMS/MMS send/receive (`SMS_DELIVER`, `WAP_PUSH_DELIVER` real
dispatch, delivery reports), MMS download/parse against a real MMSC (parser only host-tested against hand built PDUs), reject-with-message
via `RESPOND_VIA_MESSAGE`, voicemail, Bluetooth routing, system-installed priority resolution, boot-time RoleBoot, runtime permission auto-grant for
`/system/app` (live test granted by `pm grant`), vCard export, two-step delete confirmations.
Notes: other agents inject keys into the phone despite the lock (observed `input` processes and a stray volume key during a ring);
the live phone had LatinIME selected (touch keyboard swallows Up/Down); TT9 was used for tests and Latin restored afterwards.
The debug hooks (`org.kyf37.dialer.DEBUG_*`, `org.kyf37.messages.DEBUG_RECEIVE`) do nothing on `user` builds (`Build.TYPE`).
