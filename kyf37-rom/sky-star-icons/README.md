# Sky Star — cheerful kawaii icons

80 transparent 192×192 PNG icons: 64 app/common icons and 16 Settings icons.
Colors revised at the owner's request: pink, sunshine yellow, mint, peach,
lavender, turquoise and blue, with dark outlines, clouds, stars and mascots.
The phone uses 72dp Home tiles and wallpaper-adaptive text in every theme.

Choose **Settings → Appearance → Sky Star** (also Phone settings → Appearance).
Standard and Pastel Star remain available. The persistent Global setting is
`kyf37_icon_theme`: 0 Standard, 1 Pastel Star, 2 Sky Star.

Art created with the built-in imagegen tool; original and revision prompts are
saved beside the atlas. `atlas-blue-v1.png` preserves the first color draft.
`atlas.png`, `preview.png`, `icons/` and `sky-star-icon-pack.zip` are the final
deliverables. The ZIP is an image collection; the three APKs provide integration
on this custom KYF37 ROM. This is not a standalone launcher-compatible APK.

Reproduction: Windows Python with Pillow runs
`device-inspection/fix-android10-sky-star-icons.py --prepare`; WSL Python runs the
same script without arguments after the original icon and Appearance scripts.
Build Kyf37Home, Kyf37PhoneSettings, Settings using `build-locked.sh`, then run
`tools/install-sky-star-icons.ps1`. The installer keeps prior APKs for rollback.
Theme changes only presentation. Unknown future apps receive the matching star
fallback; installed launcher apps are checked against `packages.json`.

Verified on the phone on 2026-10-09: all three APK installs succeeded; D-pad
selection changed the Global value 2 → 0 → 1 → 2, and screenshots show the
corresponding Home artwork. Both Settings menus display Sky Star correctly.
The checked inventory contains 27 launcher activities, all explicitly mapped.
The final color build passed in 1:25. See `build.log`, `coverage.json`, and the
Home/Settings/Appearance screenshots. Sky Star is left selected on Home.
Wi-Fi was restored to its initial enabled state after navigation testing.

Original PNG generation and the stronger color revision both used built-in
imagegen. `generation-prompt.txt` records the layout/subjects; the final coloring
prompt is `color-revision-prompt.txt`.
