# Original Kyocera phone app: experimental Android 10 port

Owner stock Dialer resources/deodexed bytecode are platform-signed under
org.kyf37.dialerxx with a distinct provider authority. Current/default dialer is
retained. Resource IDs are mapped by name; missing legacy classes are bundled
without replacing boot classes. This test APK is not in PRODUCT_PACKAGES.

## Rebuild and persistence

After stock/compat staging, run fix-android10-native-softkeys.py, then
port-stock-dialer-android10.py (runs fix-android10-stock-call-apis.py). Audit with
audit-stock-dialer-classes.py, audit-stock-dialer-telecom.py and
audit-stock-call-migrations.py. See ../../NATIVE-SOFTKEYS.md for native bars,
physical-key policy and build/release persistence.

## Migrated operations

PhoneAccount icons, multiple-account queries, URI-based call deflection and
video callbacks use modern APIs. Receiver mute uses stock HAL parameter
rxvoice_mute_enabled=true/false. Hearing effects use voicefreq=off/mode1/mode2/mode3.
UI-active boolean and the per-call forwarding/snooze marker are migrated;
setCallFowarding is not network forwarding configuration. Standard held/ringing
call resume uses unhold/answer, without reproducing OEM greeting-in-progress state.
Single-SIM switchToOtherActiveSub remains a no-op as in the stock DSDA guard;
multi-SIM hold/unhold adaptation is not OEM local-hold parity.

Manual memo requests VOICE_CALL/AAC to private files, with 20-minute/32MB bounds,
state/error cleanup, and an explicit failure notification instead of false success.
Actual two-sided recording depends on HAL support. Automatic memo is DEFAULT OFF
(kyf37_auto_call_memo=0); production setting/provider integration remains pending.
Save/discard handles the latest pending finalized memo. One automatic attempt per
call prevents retry loops. Internal CallMemoActivity lists/plays/deletes private
memos using D-pad/OK/F1-F3 and blocks playback during calls. Manifest registered,
but original menu/provider integration is pending; no launcher entry is added.

## Remaining work

absenceMemo() is the only direct Telecom method still missing in audited incallui.
The original answering-machine path answers, routes a greeting through OEM audio
stream 11, then records. That stream number does not establish Android 10 uplink
routing compatibility. Plain answer/speaker playback was not substituted.
OEM PhoneSetting/PhoneMemo/speed-dial/blacklist providers are not proven present
or compatible merely because helper classes are bundled. Codec/reject/substate
extras default to unknown 0 when absent. Legacy answerHolding and full DSDA
behavior are not reproduced by basic public APIs.

## Offline verification

Java/dex/APK assembly and platform signing pass; 31 invocation migrations.
Class audit: 1,861 executable references, 0 missing; generic metadata anomaly
listed separately. Migration audit: 91 helper/stock-Guide calls, 0 missing descriptors;
memo activity and audio permissions verified in binary manifest. Telecom audit
lists absenceMemo unresolved. These are static checks, not call behavior tests.
No call or recording was made.

Early test APK reached permission review before the owner chose offline work.
Latest APKs have NOT been installed; current phone app remains default. Validate
launch/permissions, native softkeys, contacts/history, incoming/outgoing call UI,
audio controls, recording finalization and failures in the next authorized hardware
session. Cellular baseline is separate. Do not change default until validated.

## Live continuation — 2026-10-11
Latest test APK installed. Bare DialerApplication manifest name and absent PhoneConstants.DEBUG fixed in reproducible scripts. Application now proceeds further, but asynchronous startup fails on absent content://speed_dial/check_delete. No provider fake-success stub added, no call made, current org.kyf37.dialer default retained. See ../all-stock-app-ports/LIVE-20261011.md and crashes-live.txt. Earlier NOT installed status applies to the previous revision.

