# Kyocera Gallery port — 2026-10-11

This extends the already-migrated **original Kyocera Data Folder APK**, package `jp.kyocera.datafolder`. Its original application, resources, native libraries, original DEX files and original screens are preserved. A resource-free `org.kyf37.gallery.GalleryActivity` is added in another DEX and becomes the launcher/media entry. The original activity is explicitly reachable through **Original Kyocera Data Folder**; non-media pickers and original custom intents delegate to it.

## Implemented local features

| Feature | Implementation / limit |
|---|---|
| Photos and videos | MediaStore scan on a background executor; removable volumes retain their identity |
| Albums | Derived from actual folders, sorted by name; copy/move to existing or new albums |
| Filters and search | All, Photos, Videos, Favorites, Trash; filename/album search; newest, oldest, A–Z, size sorting |
| Favorites / hidden albums | Persist across app restarts; hiding is a display filter, not an encrypted vault |
| Batch actions | Select visible items; share, favorite, copy, move, trash or restore; per-item error reporting |
| Photo viewer | D-pad previous/next; physical zoom/pan; GIF/animated WebP playback through Android's decoder |
| Video viewer | OK play/pause, left/right seek 10 seconds, up/down media volume |
| Photo editing | Rotate, crop with physical keys, grayscale and brightness; exports a separate JPEG up to 1600px. Originals are never overwritten; export does not preserve source EXIF metadata |
| Video trim | Exports a separate MP4 with supported audio/video tracks; begins at the preceding video keyframe, not arbitrary frame-accurate re-encoding |
| Sharing / pickers | Standard content URIs, ClipData and read grants; single/multiple media picking respects the caller's request |
| Details | Name, MIME, size, dimensions, date, folder, volume and available camera/ISO metadata |
| Wallpaper | Native wallpaper manager; Home, lockscreen or both |
| Slideshow | Current photo results, 5-second interval; stops on pause/back |
| Trash | Recoverable app-private copy and atomic journal before removing the original; explicit restore/permanent delete; no automatic expiration |
| Native fallback | Original Kyocera Data Folder remains available, including its original unsupported categories / contracts |

This is a local gallery designed for the KYF37's 1 GB RAM, not a cloud/AI photo service. Cloud backup, face recognition, semantic search, secure vaults, RAW development, advanced color grading and frame-accurate video editing are not implemented. Thumbnails use a 6 MB cache, two workers and at most 24 outstanding thumbnail jobs. Stills decode to at most 1600px and animations to 854px. Trash consumes app storage; uninstalling the gallery or clearing its app data removes those recovery copies.

## Physical controls

- Grid: D-pad browse; OK open; `*` / Contacts options; Camera capture; Mail select; Browser albums/timeline.
- Selection: OK/Mail mark; `*` batch actions; Browser finish selection; Back cancel selection.
- Photo: left/right previous/next at fit, D-pad pans while zoomed; 2 zoom in, 8 zoom out, 5 fit.
- Crop: D-pad moves crop; 4/6 change width; 2/8 change height; OK applies; Back cancels.
- Video: OK play/pause; left/right seek; up/down volume; Back gallery.
- Text dialogs use the installed physical-key IME; no touch input is required.

## Build and provenance

`fix-android10-gallery.py` stages the Java sources and the existing `Kyf37StockDataFolder` ROM module. The build wrapper builds the DEX payload as a package-only target, calls `merge-kyf37-gallery.py`, verifies original-entry preservation, runs host logic checks, then builds the requested modules. The payload and test APK are not included in PRODUCT_PACKAGES. Home prefers the enhanced Gallery tile over Gallery2, while the latter remains installed as a fallback.

Build through `device-inspection/build-locked.sh <log> Kyf37StockDataFolder Kyf37GalleryTests Kyf37Home`. Do not run Android builds outside this wrapper.

The immutable port base is `kyf37-rom/all-stock-app-ports/signed-apks/Kyf37StockDataFolder.apk`; it is not overwritten. `kyf37-rom/gallery-port-report.json` records its identity and preservation checks. `verify-gallery-port.py` checks the merged APK independently, including exclusion of instrumentation code from the release. `GalleryLogicTest.java` checks filename/path validation and crop edge cases. `GalleryInstrumentation.java` uses only newly generated synthetic fixtures for destructive-operation tests; the test video is a generated 5-second 160×120 color pattern with silent AAC audio.

Deployment and hardware results are recorded below after testing. No ROM/recovery flashing, reboots, SIM PIN input or userdata clearing is needed for this app update.
