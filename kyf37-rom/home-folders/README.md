# Home folders — 2026-10-11

Native launcher folders use the existing three-column icon grid and focus theme.
Folder icons contain a preview of up to four member icons. Opening a folder shows
its title and the same app grid. OK/click opens a folder/app; numbers 1–9/0 select
the first ten entries within the current grid. Back closes the folder and restores
its Home selection; Home intent closes the folder. Returning from an app normally
keeps the current folder. Empty folders can be opened and managed.

Press **\*** or **hold OK** on a tile to manage folders:

* New folder: name it; the selected app is moved into it.
* Move app to folder / Home: choose its destination.
* Rename folder, or remove it with confirmation. Removing a folder returns its
  apps to Home; it does not uninstall apps or delete their data.

Layout is private SharedPreferences JSON (`folders/layout`) keyed by exact
launcher component names. It survives launcher restarts and data-preserving APK
or ROM updates. Uninstalled members are hidden but their membership is retained
for reinstalls. An app appears once, in Home or its assigned folder.

First run seeds **Kyocera Apps** with installed launchable Camera, Calculator,
Character Check, Data Folder, Notepad, Sound Recorder, barcode Reader and the
isolated stock dialer. Provider/helper APKs have no launcher entries. Seeding runs
once; later user moves/renames/removals are retained. This grouping does not fix
the known Notepad editor or experimental dialer speed-dial-provider blockers.

## Source / build / installation

`device-inspection/fix-android10-home-folders.py` patches both Home template and
current source; `Kyf37HomeFolders.java.inc` holds the reusable implementation.
Build wrapper applies it after older navigation/Home scripts. Existing Home image
hash validation covers the next newly built ROM. No existing ZIP modified.
Implicit fixed shortcuts are made explicit using their resolved activity so
Camera and other pinned entries have a real component for folder membership.
Clock-removal, icons, wallpaper contrast, focus, quick keys and native-only bar
policy are retained. No generic footer is added.

Locked build: `build-locked.sh /home/pablo/home-folders-build-final.log Kyf37Home`.
APK: `Kyf37Home.apk`; installer: `tools/install-home-folders.ps1`.
Installer fails fast if another session owns the phone; otherwise backs up the
current launcher and installs with `adb install -r -d`, without flashing/remount.
Rollback: the same script with `-Rollback`, preserving layout/app data.

## Verification / current limits

Build/source checks are recorded beside the APK. Live installation and D-pad
testing are pending: radio-bands acquired and renewed the shared phone lock while
this change was being built. The queued lock acquisition was canceled; no phone
input, launcher installation, preference change or lock takeover was performed.
The installed launcher therefore still has its previous behavior.

Next authorized hardware check: open Kyocera Apps with OK and its numbered
shortcut; verify members are absent from root; launch Calculator from the folder;
Back to folder then Home; test * and hold-OK; create/rename a temporary folder,
move an app to it and back, confirm removal keeps the app; restart launcher and
verify membership persists; check all three icon themes and existing shortcuts.
Use the phone lock and preserve the before APK. Never claim these checks passed
from the APK build alone.
