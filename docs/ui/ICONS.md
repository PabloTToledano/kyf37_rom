# Pastel Star icon pack — 2026-10-08, 22:28 CEST

Owner requested a custom pack matching the attached pink/blue kawaii icon sheet,
covering all installed and included apps plus common apps.

Completed: 64 transparent 192×192 icons generated with the built-in image tool.
Assets, preview, generation prompt, package map, appfilter XML, coverage report,
ZIP, compiled launcher, and previous launcher APK are saved under
`kyf37-rom/pastel-star-icons/`. The artwork has pink/blue fills, rose outlines,
yellow stars, and small pink mascots. Common apps retain recognizable symbols.

Coverage: 27 launchable activities on the live phone, none mapped to the generic
fallback. 165 installed packages inventoried; nonlaunchable services and overlays
have a generic mapping. Pending `org.kyf37.tv` and `jp.co.fsi.fs1seg` are mapped.
Common messaging/social/media/navigation apps are mapped too. Unknown future
packages get the custom star badge, so Home never shows an unthemed app icon.

Integration: `device-inspection/fix-android10-pastel-icons.py` is idempotent.
It stages the pack in Home assets, adds `PastelIcons.java`, patches both Home.java
and the quick-keys source template, and sets Home's own manifest icon. The helper
loads a bundled package map and caches drawable states. No framework patch,
network call, extra permission, background service, or modifications to other
app APKs. Scope is launcher icons, not notifications or Settings app lists.

Build: `build-locked.sh /home/pablo/pastel-icons-module-build.log Kyf37Home`
passed with `BUILD_EXIT=0`, 13 tasks, 16 seconds. The wrapper was enhanced by
another task to accept module arguments during this session. An earlier queued
invocation failed because those shell files changed while it was waiting;
the fresh module build passed. No build-wrapper edits were made by this task.

Hardware VERIFIED: `adb install -r` succeeded; Home is current focus;
`phone-home.png` shows the first page, `phone-apps.png` shows the lower page with
microG, infrared, Music, Notepad, Phone settings, Sound Recorder, TikTok and TT9.
D-pad down scrolling worked; Back returned to the first tile. No `PastelStar`
errors or `FATAL EXCEPTION` in the recent logcat check. `sys.boot_completed=1`.
Phone lock released. Wallpaper and keypad behavior preserved.

Reinstall: `tools/install-pastel-icons.ps1` validates 64 embedded icons, takes
the cooperative phone lock, backs up the previous APK if needed, installs the
updated launcher, and captures a screenshot. Rollback with `adb install -r`
using `Kyf37Home-before-pastel.apk`. No ROM flash or partition writes performed.

## Settings extension — 2026-10-08, 22:38 CEST

The owner additionally requested icons for Settings. Added 16 illustrations
(battery, display, speaker, storage, privacy, system, support, printer, mobile
data, hotspot, airplane, vibration, USB, rotation, language, notification bell).
Combined downloadable ZIP now contains 80 PNG icons. Original atlases and both
generation prompts are retained in the pack directory.

`fix-android10-pastel-settings-icons.py` reproducibly applies 67 resource aliases
in Android Settings, including its 15 homepage categories. It adds illustrations
to display preferences and Bluetooth/connection entries, and image columns to
all 14 rows of `Kyf37PhoneSettings`, patching that app's regeneration template
too. The two application icons are also updated. Category wrappers have fixed
24/32/48 dp sizes and preserve multicolor art instead of applying vector tints.
Status indicators and toolbar controls retain their original behavior.

Build through `build-locked.sh /home/pablo/pastel-settings-build.log Settings
Kyf37PhoneSettings` passed: `BUILD_EXIT=0`, 2:38. Android Settings APK signature
verification passed. Both APKs installed successfully with `adb install -r`;
no ROM flash. Previous APKs are saved for rollback. Installer:
`tools/install-pastel-settings-icons.ps1`.

Hardware VERIFIED: `phone-settings-main.png` shows network, connected devices,
apps, battery, display and sound icons in full pastel color.
`phone-settings-keypad.png` shows the first eight Phone settings rows with icons,
numeric shortcuts, current values and focus highlight correctly laid out.
Initial captures were black because the display was asleep; wake + dismissing
the unlocked keyguard restored valid screenshots. Installer now wakes the screen
before capturing. No lid state or setting toggles were changed for those captures.

Recent logcat contained no fatal exception, resource-not-found, or inflation
error. Lower submenu/scrolling checks were queued but cancelled before acquiring
the phone lock because another hardware task held it; those pages are source-
and build-verified, not visually verified. This task released its own phone lock
after installing and capturing the two main menus.

## Appearance switch and adaptive Home — 2026-10-08

Supersedes the always-on pack behavior above. Home and both Settings apps now
share a persistent Standard/Pastel Star choice, exposed at Settings → Appearance
and Phone settings → Appearance. Original Android Settings XML art is preserved
from the tracked source and selected by a resource wrapper; Home uses original
package icons when Standard is selected. Phone settings hides its icon column in
Standard. Existing first-ten digit shortcuts are unchanged; Appearance is a new
last row. Theme selection changes icons, preserves the wallpaper, and uses the
shared `Settings.Global.kyf37_icon_theme` value (0 Standard, 1 Pastel; default 1).

Home icons enlarged from 48 to 72 dp, grid rows 110 dp. Text color automatically
chooses dark ink or white using the wallpaper beneath each label, clock and date;
refreshes on scrolling, resume and wallpaper events. A small 96×170 sample is
retained. Live wallpapers use published colors. Contrast regression checks passed
for bright/dark, blue and mixed backgrounds.

Source script: `device-inspection/fix-android10-appearance-switch.py` (run after
both icon staging scripts); helper source templates have `Kyf37AppearanceSettings`,
`Kyf37ThemeDrawable`, `Kyf37WallpaperContrast`, and `Kyf37ContrastMath` names.
Home permission allowlist and default storage permission grant are staged in the
device tree for future builds. The live installer grants wallpaper read access
on the current older ROM. Phone settings requests WRITE_SECURE_SETTINGS for the
platform-signed theme writer; granted=true was observed.

Builds passed: all three app modules 1:43, display-coordinate correction Home
14 seconds, wallpaper-access Home 1:02. All three APKs updated successfully with
ordinary `adb install -r`; no ROM flash. Initial installation failed while the
phone was still booting after another task's reboot; retry after boot_completed=1
succeeded. Older APKs remain as rollback copies.

Hardware VERIFIED: D-pad/OK changed 1→0 in the Appearance UI; native Home icons,
original Android Settings category icons and text-only Phone settings rendered
correctly. Phone settings' Appearance row opened the chooser; D-pad/OK changed
0→1 and restored the pack on Home and Android Settings. Larger icons and dark
text on the bright owner wallpaper are visible in screenshots. The log confirmed
real wallpaper sampling, not just a fallback color. Dark-background decisions
are host-tested; a dark wallpaper was not applied to the phone. Left in Pastel
mode on Home; own phone lock released.

Artifacts and screenshots: `kyf37-rom/appearance-switch/`; installer:
`tools/install-appearance-switch.ps1`. This supersedes older APK installers when
reinstalling the current appearance controls.

## Sky Star — colorful alternative, 2026-10-09
The owner's sky/cloud/Kirby/blue-duck reference was used to create a new 80-icon
atlas with built-in imagegen, then revised for a stronger cheerful rainbow palette.
Final art was cropped from genuine alpha gutters into 192px transparent PNGs.
Sky Star joins Standard and Pastel Star in Settings / Phone settings → Appearance.
The persistent key is 0/1/2; the existing large Home icons and adaptive text remain.
Home's icon cache now separates themes. Settings' resource wrapper supports the
third choice; Phone settings selects the matching illustration array.
Final build passed (1:25), three live APK installs passed, and on-phone D-pad
selection/readback verified 2 → 0 → 1 → 2 with Home screenshots for each theme.
Sky art was verified in both Settings menus. Current 27 launchable activities all
have explicit mappings. The phone is left on Home with Sky Star selected.
Source: `device-inspection/fix-android10-sky-star-icons.py`; live installer:
`tools/install-sky-star-icons.ps1`; assets, ZIP, APKs, previous-APK backups,
prompts, logs and screenshots: `kyf37-rom/sky-star-icons/`.
The pack ZIP is a reusable PNG collection, not an installable universal theme APK.
No reboot-persistence test was performed; the selection uses Settings.Global's
persistent DB. A WSL prepare attempt lacked Pillow; Windows Python/Pillow handled
cropping. CLI activity testing needed --activity-clear-top to avoid bringing the
app's entire existing task forward; Wi-Fi briefly toggled during that mistaken
navigation and was restored to its initial enabled state before finishing.

## 2026-10-11 — fourth theme and wallpaper
Kyocera Classic (key 3) uses original Kyocera launcher/app and stock framework
symbols inside custom white/sky tiles with gold detail. Added alongside Standard,
Pastel Star and Sky Star in Appearance, both Settings menus and Home. Owner's new
sky/castle image is the explicit Home/lock wallpaper and next-build default.
Reproduction, original art provenance, APKs, screenshots and final verification:
kyf37-rom/kyocera-classic/README.md. Scripts prepare-kyocera-classic.py and
fix-android10-kyocera-classic.py; tools/install-kyocera-classic.ps1. Stock artwork
is proprietary owner-ROM material, not an open-licensed redistribution pack.
