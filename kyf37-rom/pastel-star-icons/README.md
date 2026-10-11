# Pastel Star — KYF37 icon pack

80 transparent 192×192 PNG icons (64 app icons + 16 Settings illustrations), created with the built-in image-generation tool
on 2026-10-08, inspired by the owner's pastel kawaii reference. Pink and baby-blue
fills, rose outlines, yellow stars, small pink mascots. The original generated
atlas is preserved as `atlas.png`; individual assets are cropped from it.

`preview.png` shows the app icons; `settings-preview.png` shows the additional Settings icons. `pastel-star-icon-pack.zip` includes PNGs,
`appfilter.xml`, package mappings, and the coverage report. The XML contains exact
activity mappings for the 27 launchable apps detected on the connected phone.
Common apps have package mappings; third-party launchers may need additional
activity mappings for their specific versions.

KYF37 Home uses the bundled package map directly. All 27 current launchable apps
have specific icons, including TikTok Lite, Libre Camera, Aurora, microG, TT9,
the Kyocera apps and keypad settings. The ROM's pending One Seg TV app and launcher
are also covered. Common social, messaging, media, navigation and utility apps
have icons. Unknown future apps use the themed star badge automatically.
Background services and overlays are mapped to a generic icon; they have no
home-screen tile. The base pack changes launcher artwork. The extension below
adds icons to the two Settings menus; other apps' APKs remain untouched.

Android Settings and Phone settings extension APKs are installed and verified on
the phone. Screenshots: `phone-settings-main.png`, `phone-settings-keypad.png`.
Reinstall with `tools/install-pastel-settings-icons.ps1`; prior APKs are saved as
`Settings-before-pastel.apk` and `Kyf37PhoneSettings-before-pastel.apk`.

Reproduce asset extraction on Windows (Pillow):

    python device-inspection/fix-android10-pastel-icons.py --prepare

Apply the source patch in WSL:

    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-pastel-icons.py

Build through `device-inspection/build-locked.sh`. For live testing, install only
the resulting platform-signed `Kyf37Home.apk` using `adb install -r` while holding
the cooperative phone lock. No ROM flash is required.

Hardware verification completed on 2026-10-08: the updated launcher is installed,
all current apps display the themed icons, D-pad scrolling and Back work,
and recent logs contain no icon-loading errors or fatal exception. Screenshots
are `phone-home.png` and `phone-apps.png`. Use `tools/install-pastel-icons.ps1`
to reinstall. The previous launcher is `Kyf37Home-before-pastel.apk`.

The Settings extension rebuilds Android Settings and Phone settings from source
to add illustrations inside both menus and their application icons. Its script,
`device-inspection/fix-android10-pastel-settings-icons.py`, stages resource aliases,
preference icons, and an image column in the 14-row keypad menu. Existing toggle
and navigation behavior is preserved. It does not replace other apps' icons in
Android's app-management list or change toolbar and status indicators.

Source regeneration: the quick-keys template is patched too. If another script
replaces Home.java, rerun the icon fix afterward. The owner boot-signing key is
not used for the launcher APK.
