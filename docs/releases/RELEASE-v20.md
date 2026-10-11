# KYF37 Android 10 Go v20

Owner-specific release for serial 981108631314. Built 2026-10-11 on top of v19 (first-boot verified).

## New since v19
- **Keitai apps:** Phone (org.kyf37.dialer), Messages (org.kyf37.messages), Contacts (org.kyf37.contacts), keypad-first, keitai look,
  default dialer / default SMS app. Verified live with local data only; real calls/SMS need the radio.
- **SystemUI shade/quick settings:** keypad-operable (numbered tiles, digit shortcuts, Clear all row), the shade button bar removed.
- **Blue system accent** instead of Lineage teal (verified in framework-res: #1e6fd9 / #7ab0f7 / #1555b0).
- **TT9 is the default keyboard** (one-shot first-boot service; the live phone already uses TT9).
- Release gate (check-release-image.py) passed: no TV apps, no public.libraries-kyocera.txt.

## Known gaps
- Cellular does not register (modem never starts NAS/UIM/WMS/VOICE/WDS); see MODEM-STATUS-20261009.md.
- Not booted on hardware before packaging; apps' boot-time role takeover and /system/app permission auto-grant are untested.
- SystemUI loop checks not finished (themes, brightness slider effect, heads-up, lock screen, power menu, volume panel).
