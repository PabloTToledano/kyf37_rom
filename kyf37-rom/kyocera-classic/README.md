# Kyocera Classic and Android 10 stabilization — 2026-10-11

New Appearance option: **Kyocera Classic** (`kyf37_icon_theme=3`). Original Kyocera
launcher/app and stock framework glyphs sit on custom rounded white/sky tiles
with a small gold accent. Standard, Pastel Star and Sky Star remain selectable.
80 resource names cover Home and both Settings menus; artwork-sources.json records
every source APK/entry. 53 categories have direct semantic stock artwork; remaining
categories share stock application/tool fallback art. This is a personal ROM
adaptation of proprietary owner-supplied stock assets, not freely licensed art.

The supplied sky/castle wallpaper is preserved as wallpaper-original.png and
resampled to the panel's 480x854 aspect ratio. Source stages the ROM default and
Home's explicit home/lock wallpaper setter. Normal launcher starts never reset a
user-selected wallpaper. Folder headings now use wallpaper contrast sampling,
matching app labels, so they remain readable on this light image. Pinned Camera
now targets the installed Camera2 package instead of the ambiguous Android
resolver, preventing a duplicate chooser tile. The original Kyocera camera stays
in the stock-app folder. New port/native-app package mappings cover all themes.

The density-specific hdpi wallpaper is also overridden: testing found that the
older nodpi-only device overlay lost to Lineage art in the packaged APK.

## Baseline audit
A v20 ZIP and RELEASE-v20.md exist. A separate full v21 build appeared during
this session at /home/pablo/v21-build.log and owns the shared build lock; no
finished v21 ZIP/candidate was present at inspection. The final theme build queues
behind it. Source corrections landed while that build ran: its packager must use
the current APK/image hash gates rather than assuming the first image includes
all final corrections. The live phone reports Android 10, build Oct 9 20:25:01, matching the
v19 baseline identified by MODEM-SIGNAL-DATA-20261011.md, plus later live fixes.
Do not describe it as a verified v21 installation. Latest radio notes supersede
old missing-modem-channel reports: registration and GPRS data work after the
SETUP_DATA_CALL crash fix. Calls/SMS/VoLTE remain outside this verification.
Current brightness test: settings 40 -> both lcd-backlight and backlightinfo 40;
180 -> both 180. Restored original 10, manual mode 0. This verifies the control
path, not a human assessment of perceived brightness.

## Reproduction
- Windows: python device-inspection/prepare-kyocera-classic.py (Pillow; reads stock
  APKs through the Ubuntu WSL share; no downloads or generative art).
- WSL: python3 device-inspection/fix-android10-kyocera-classic.py.
- Build: device-inspection/build-locked.sh ~/kyocera-classic-final-build.log
  Kyf37Home Kyf37PhoneSettings Settings framework-res.
- Build wrapper runs the staging script after older generators and Home folders.
- Live: tools/install-kyocera-classic.ps1 backs up APKs, installs normal app
  updates, selects the theme, and explicitly applies the supplied wallpaper.

Existing ZIPs are unchanged. The next fresh image includes source/default assets;
framework-res itself must use the normal validated release pipeline, never an
isolated live framework APK replacement. Runtime wallpaper uses WallpaperManager.

## Verification
Final build and live results are recorded in verification.txt. The three final
application APKs are installed and their on-device SHA-256 values match. Home
restart retained the selected theme and eight-member folder. Final screenshot
checks confirm the direct Camera icon, removed duplicate and dark folder heading.
Number 6 opens Kyocera Apps; Back selects that folder again. No phone
reboot, ROM/boot/recovery flash, radio changes or data wipe is needed.


## Runtime baseline and limits
ro.config.low_ram=true; ART JIT=true; 384 MB zram active. Home total PSS was
33,323 KB after cycling themes; this is a baseline, not a measured speedup.
System had about 104 MB free, data about 2.9 GB. No CPU/GPU overclock or memory
policy change was justified by these readings.
Installed outer APK already contains timeout settings and Bad Apple support.
Injected lid-close: main display Asleep at 2s and 13s; outer framebuffer hashes
differed after its default timeout. Lid-open restored true. This is software
verification, not direct observation of panel darkness or audible playback.
Native lockscreen screenshot confirms supplied wallpaper and stacked Pixel clock;
Up + OK returned through native Keyguard to Home. Credential verification was
not tested; no PIN/password was entered or bypassed.
The attempted folder-name dialog check used injected text; TT9 changed the text
and kept focus in the editor on Down. Tab reached Cancel and cancellation was
verified; no temporary folder was saved. Full create/rename/move/remove D-pad
coverage remains pending and is not implied by the successful folder opening,
Calculator launch and * menu tests.
Existing isolated stock dialer crash at 08:53 predates these tests; no new crash
entry was observed during theme/folder tests. Memo editor and speed-dial provider
remain separate stock-port blockers.

APK rollback restores the previous three apps and icon selection; the supplied
wallpaper remains selected. The previous wallpaper was the system default (no
wallpaper image file was present to back up), and can be reset in Wallpaper
settings. Folder preferences are preserved; no app data is cleared.


## Release integration
The separate v21 full build completed successfully in 17:05. Its first image was
built before the final Camera/folder/default-wallpaper corrections. These are now
compiled and source staging is in the normal build wrapper. A fresh systemimage
build and current image/asset hash gates are required before its release is
packaged. This session did not rebuild or flash a ZIP, boot, recovery or framework
image. framework-res.apk here is a future-release artifact, not a live installer
input. Lineage's existing hdpi/nodpi common-overlay images are also patched because
that common overlay links after the device overlay in this tree; exact packaged
handset pixels now pass verification. Unchanged icon assets are copied only when
content differs, avoiding unnecessary resource rebuilds on script replay.
