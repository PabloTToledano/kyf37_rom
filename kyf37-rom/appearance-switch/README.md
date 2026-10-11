# KYF37 appearance controls

Open **Settings → Appearance**, or **Phone settings → Appearance**. Choose
**Standard** or **Pastel Star** with the D-pad and OK. Selection is saved in
`Settings.Global.kyf37_icon_theme` (0 Standard, 1 Pastel Star), survives process
restarts/reboots, and applies to Home and both Settings menus. Default is the
already-installed Pastel Star theme; changing theme preserves the wallpaper.

Home icons are 72 dp instead of 48 dp, with 110 dp grid rows and three columns.
Digit shortcuts and all app tiles remain available by scrolling. Home reads
original package icons in Standard mode and the bundled pack in Pastel mode.

Android Settings retains its original drawable XML from the tracked Lineage
source, alongside the custom assets. A small drawable wrapper selects the art
using the shared setting and observes changes. In Standard mode, Phone settings
returns to its original text-and-digit rows; Pastel Star displays its icon column.

Home samples a small 96-pixel-wide image of the current wallpaper, chooses dark
or light text separately for the clock/date and visible app labels, and updates
after scrolling and wallpaper changes. Contrast uses sRGB relative luminance and
contrast ratios, with a score combining median and lower-quartile contrast for
mixed backgrounds; a light/dark shadow helps across busy patches. Live wallpapers
use their published main color. No periodic wallpaper polling or background
service is added.

The source patch is `device-inspection/fix-android10-appearance-switch.py`. Run
it after the two Pastel Star staging scripts. It also patches launcher/settings
regeneration templates. The Home wallpaper read permission has an explicit
privapp allowlist staged in the device tree for future ROM builds; Phone settings
requests the platform-signed permission needed to persist the shared theme.

On the current older ROM, wallpaper-internal access is not granted without the
new system allowlist. Home therefore also declares wallpaper's public storage
read permission, which the live installer grants. A default-permissions entry
is staged for future ROM builds. Wallpaper sampling was verified in the live log
(`Wallpaper sampled: 96x170`) after this grant.

Build:

    device-inspection/build-locked.sh /home/pablo/appearance-switch-build.log Kyf37Home Kyf37PhoneSettings Settings

This build passed in 1:43 (`BUILD_EXIT=0`). Contrast regression checks passed
for solid light/dark, light/dark blue, and mixed backgrounds.

Install the three compiled APKs with `tools/install-appearance-switch.ps1`, which
backs up existing APKs, holds the phone lock and performs ordinary `adb install -r`
updates. The `*-before-appearance.apk` files are rollback copies. No ROM flash.

Hardware VERIFIED on 2026-10-08: D-pad/OK chose Standard in Appearance and the
shared setting became 0; Home displayed native icons, Android Settings displayed
its original category art, and Phone settings hid its icon column. Navigating
through Phone settings to Appearance and choosing Pastel Star saved 1 and restored
the pastel icons in Home and Android Settings. The clock/date and labels displayed
dark ink on the bright owner wallpaper. Larger icons and scrolling were visible.
The phone is left in Pastel Star mode on Home; this task's phone lock is released.

Screenshots: `appearance-options.png`, `phone-appearance-entry.png`,
`home-standard.png`, `home-pastel.png`, `settings-standard.png`,
`settings-pastel.png`, `phone-settings-standard.png`. Light/dark and mixed wallpaper
decisions were also tested in host-side Java; a dark wallpaper was not applied to
the phone. Wallpaper file and unrelated settings were preserved.

An initial install returned a package Binder transaction error while the phone
was still booting after another hardware session. Installation succeeded once
`sys.boot_completed=1`. The Home access follow-up build also passed (1:02).
