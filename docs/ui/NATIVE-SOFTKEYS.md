# Native Kyocera softkeys and persistent UI policy - 2026-10-09

The owner requested no generic bottom bar anywhere. Only supported Kyocera apps
display their app-owned softkey guide. Kyf37Home no longer has the large clock;
the status-bar clock and launcher date remain.

## Source implementation

`fix-android10-native-softkeys.py` restores the full original KCfpSoftkeyGuide
classes: dynamic text/icons, enabled state, priority merging and XML resource
loading. Kyf37SoftkeyBridge replaces the old Window extensions, draws original
stock SystemUI artwork with 116/88/116 column proportions and two 32dp rows,
and reserves 64dp inside the app content. It resolves XML names against the real
resource package, including the renamed dialer. Dialog button labels delegate to
the bridge. Compile-only Guide declarations are removed before dex packaging.

Visible footer whitelist: Kyocera Camera, MemoPad, barcode Reader, sound recorder
and manager, original afphome, experimental org.kyf37.dialerxx, and archived
MobileLight. MobileLight remains excluded from the ROM product and removed for
phone user 0; this does not restore it. The current Home, Settings, replacement
flashlight and other apps have no bottom bar. MemoPadProvider has no UI.

Later offline all-app continuation extends the app-local bridge to candidate APKs
carrying an exact `assets/kyf37-native-softkeys/package.txt` marker. A guide is
attached only when requested by the native app. Candidate key-policy entries are
limited to apps referencing the native softkey API in their app DEX; unrelated
services/apps retain generic keypad controls. This does not select or install any
candidate. `fix-android10-native-softkeys.py --compat-only` rebuilds helper DEX
without rewriting the six existing app APKs. Full ordinary systemimage builds
still refresh those existing APKs through the original bridge pipeline.

`fix-android10-native-softkey-policy.py` lets supported native apps receive their
own F1-F4 events, without replacing them with global Menu/Pointer/Home actions.
Other apps retain existing keypad navigation. End/call/lid behavior is separate.

`fix-android10-native-only-bars.py` removes generic SystemUI view insertion, sets
navigation dimensions to zero and config_showNavigationBar=false, and forces
KYF37 DisplayPolicy navigation false even if legacy init sets qemu.hw.mainkeys=0.
It removes only Home's time widget and contrast reference; date contrast remains.

## Persistence across ROM builds

Changes are ROM source patches, not runtime preferences. build-locked.sh calls
build-kyf37-android10.sh, which restores native softkeys for systemimage/native APK
builds, reapplies native key policy, then applies native-only-bars last on every
build. Older appearance/footer scripts cannot restore unwanted UI in a new build.
Do not remove this final enforcement or use an unwrapped build for releases.

Reconstruction requires existing owner stock backups, deodex/compat stages, local
JDK8/SDK7/dex tools and aapt2. Stage stock apps and launcher/appearance first, then:

1. fix-android10-native-softkeys.py AFTER build/patch-kyocera-compat-smali.py.
2. fix-android10-native-softkey-policy.py.
3. fix-android10-native-only-bars.py LAST.
4. Locked build: SystemUI Kyf37Home framework-res services KyoceraCamera MemoPad
   MemoPadProvider Reader kc_soundrecorder kc_soundrecorder_manager; or systemimage.
5. Normal validated, owner-signed ROM release with rollback retained.

validate-android10-images.py hashes image copies of framework-res, SystemUI,
Kyf37Home and six shipped native app APKs against current build outputs, rejecting
stale release inputs. Existing userdata/preferences survive normal ROM updates;
no wipe is required. Framework/services updates need matching validated ROM/ART
artifacts, not isolated live jar replacement.

The same image gates include the replacement Kyf37Flashlight and
Kyf37PhoneSettings APKs. Existing icon/theme, notification/QS, lockscreen and
focus source changes remain in the build tree; their reconstruction instructions
are in ICONS.md, KEITAI-UI.md and KEYPAD.md. Reapply
fix-android10-visible-focus.py and fix-android10-keypad-panel.py after older UI
passes when reconstructing, then the native-only policy last.

## Verification

native-only-bars ran twice successfully (idempotence). Native bridge Java/dex
compilation and seven APK reassemblies pass. Earlier services/native app build
passed in 2:31; final builds are logged under kyf37-rom/keypad-focus/:
native-only-bars-build.log and native-softkeys-final-build.log.
Final locked builds passed: SystemUI/Home/framework-res in 2:53 and
services/native apps in 2:01. Compiled framework resources show
config_showNavigationBar=false and default navigation dimensions 0dp. Native
bridge and exact stock-artwork verification passed for all six shipped modules.
Ten offline artifacts, logs and SHA256SUMS are saved in kyf37-rom/native-softkeys/.
Latest changes are OFFLINE and not installed, per owner instruction. Default
dialer is unchanged. Next hardware session must verify labels, F1-F4 actions,
dialogs/content clearance, absence of a footer elsewhere, home clock removal,
notifications/QS and lockscreen after a matching ROM update.

The original phone test port remains experimental. See
kyf37-rom/stock-dialer-port/README.md for call API migrations and unresolved
answering-machine/provider integration. Bundled helper classes do not establish
that OEM PhoneSetting/PhoneMemo/blacklist/speed-dial providers work.
