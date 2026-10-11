# KEITAI-MATERIAL: Material You look for the KYF37 SystemUI (2026-10-11)

Owner request: "as modern looking and Material You as possible while keeping the cute keitai style".
Scope: SystemUI only (shade, quick settings, notification cards, footer, selection outline, volume dialog and power menu theme).
No framework-res change, no flash. Live-installed APK: `kyf37-rom/systemui-loop/apk/SystemUI-m8.apk`
sha256 `5a4d63af8ccfbbdedfe5e9a98d91438e46934262726498e8eef12966c850675d` (installed at `/system/product/priv-app/SystemUI/SystemUI.apk`, /system left read-only).

## Reproduce / rollback
* Source: `device-inspection/fix-android10-systemui-material.py` (+ `Kyf37Material.java.txt`, `Kyf37MaterialPreview.java.txt`),
  chained after `systemui-shade` in the `kyf37_nav` loop of `build-kyf37-android10.sh`; idempotent.
* Build: `wsl -d Ubuntu -- bash /mnt/c/.../device-inspection/shade-iter.sh <name>` (runs `build-locked.sh <log> SystemUI`, signs, stages `SystemUI-<name>.apk`).
* Install (phone lock `sysui-material`): `bash tools/install-systemui-loop.sh kyf37-rom/systemui-loop/apk/SystemUI-m8.apk`.
* Rollback: `bash tools/install-systemui-loop.sh kyf37-rom/systemui-loop/apk/SystemUI-iter8.apk` (previous loop SystemUI) or `SystemUI-v19-original.apk`.
  Intermediate builds m1..m7 are kept next to it. The first m3 crash-looped SystemUI (footer settings button background must be a RippleDrawable,
  `QSFooterImpl` casts it); it was rolled back to m2 within a minute and fixed before m3 was rebuilt.
* Screens: `tools/material-shots.sh <dir> [night]` (real shade walk), `tools/material-preview.sh <dir> <name> <sel> [night]` (see Preview).

## Design language
| | Material You (Android 12 style) | Keitai (kept) |
|---|---|---|
| Shape | 28 dp cards (QS panel, tiles), 20 dp notification cards, pill chips/buttons (battery chip, Clear all), circular footer buttons | digit badges, star sparkle accents |
| Colour | tonal palette of the system accent #1E6FD9 (dark #7AB0F7): active tile = primary container + primary icon circle, inactive = surface variant, cards on a tinted backdrop, no hard outlines | pastel icon themes (Standard / Pastel Star / Sky Star) untouched |
| Type | Roboto (sans-serif-medium) for date, tile labels, status text; 19 sp date, 13 sp tile labels. No Google Sans / Roboto Flex in this ROM | |
| Selection | thick rounded outline in the Appearance focus colour (default Sky blue) + translucent tonal fill + inner white hairline; follows the 7 palettes, never yellow | unmistakable D-pad focus |
| Motion | 150 ms tonal colour change of tile card and circle (existing QS_ANIM_LENGTH), no blur, one rounded drawable per tile | |

Tokens (`res/values/colors_kyf37_material.xml`, `values-night/...`, names `kyf37_m_*`), light / dark:
primary #1E6FD9 / #7AB0F7, on_primary #FFFFFF / #00305F, primary_container #D8E6FF / #17407A, on_primary_container #001C3F / #D8E6FF,
backdrop #DFE6F2 / #0E1116 (drawn at 94% alpha so the wallpaper only hints through), card #F6F8FD / #1C2028, card_variant #E3E9F5 / #2A303A,
card_high #D0D9EA / #3A4250, on_surface #191C22 / #E3E6EE, on_surface_variant #43495A / #C0C6D4.

What changed:
* `Kyf37Material.java` (SystemUI): tokens, tile card (`TileCard`, active tiles carry a small four-point sparkle), selection drawable.
* QS tiles: rounded tonal card per tile, tonal circle/icon/label colours, 108 dp tall cells, wider cells (margins 10 dp), dual-target caret removed
  (labels no longer truncated; detail pages still open with hold-OK), digit badges restyled (primary circle with card-coloured ring; smaller on the 48 dp header chips).
* Notification rows: 20 dp rounded tonal cards, 6 dp gaps, stroke removed, every card fully rounded; "Clear all" is a primary-container pill.
* Header: 19 sp medium date, battery readout in a pill chip; QS panel is a 28 dp card; footer edit/settings are circular tonal buttons; brightness track 10 dp thick.
* Themes: SystemUI themes carry the blue accent themselves (`colorAccent`, `colorControlActivated`) so the volume slider, bouncer buttons and dialogs are blue
  even though the live framework-res still holds the old teal until the next ROM flash; volume dialog and dialogs 28 dp, power menu uses the card tokens.
* Empty "no notifications" state gets the sparkle.
* Chain order: `systemui-shade` rewrites `Kyf37KeitaiKeys.java` and the backdrop on each build and the material script re-patches them (tag `kyf37-material`).
  `fix-android10-focus-theme.py` looks for the string `Kyf37FocusTheme.selection` in Keys: the patched line keeps it in a comment on purpose.

## Preview harness (userdebug only)
The test phone shows a SIM PIN prompt (radio work; nobody entered the PIN), so the keyguard bouncer covers the real shade on every wake and D-pad keys go to the PIN pad.
To still see real pixels the script patches the exported `MLandActivity` (Easter egg): with extra `kyf37_preview` on a debuggable build it renders the real
`QSTileBaseView` / `QSTileView`, card, selection and notification-card drawables (`Kyf37MaterialPreview`). It runs in the separate process
`com.android.systemui:sweetsweetdesserts` (kill it after installing a new APK; `material-preview.sh` does). It does nothing on user builds.

## Honest status
Verified on hardware (screenshots in `kyf37-rom/systemui-material/`: `before/`, `iter1..5`, `final/`):
* the real shade, QS and notification list behind the SIM-PIN keyguard (light and dark, partly covered by the PIN pad), volume dialog, power menu;
* real tile, card, selection and notification-card views in the preview, light and dark; selection on a tile, a header chip and a notification card;
* SystemUI stable after install, `/system` read-only again, FATAL counter unchanged apart from the m3 footer crash that was rolled back.

NOT verified: the D-pad walk of the real shade (selection, digit shortcuts, Menu/F1, hold-OK, Clear all, Back/Clear semantics) because of the PIN keyguard;
those code paths are unchanged apart from the foreground drawable and badge drawing. The lock screen clock card (modern-lockscreen script) was not restyled and
could not be seen; heads-up (uses the same card) not seen; Edit-tiles and detail pages only inherit the theme/accent changes; status-bar icons are not restyled;
the brightness thumb is unchanged. Dynamic wallpaper colour (Monet) is not implemented (no such API in Android 10): the palette derives from the fixed accent.
Re-run `tools/material-shots.sh` and `tools/test-systemui-keypad.sh` once the SIM PIN is entered or the SIM removed.
The focus theme setting on the phone was left at 0 (Sky blue); it was 1 (Pink) before this session.
Performance: no blur or shadow added; per-tile cost is one rounded rect (plus a tiny path); animations reuse the existing 150 ms animator. Not profiled on hardware.
