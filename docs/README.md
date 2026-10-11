# Documentation index

Start with `../KYF37-PROJECT.md` (current state, rules, workspace map, build/flash). Everything here is detail.

| Folder / file | Contents | Status |
|---|---|---|
| `FIXES.md` | Root cause and reproducing script for every fix, with verification limits | current, extended 2026-10-11 |
| `CHANGELOG-2026-10-11.md` | Detail sections: Home, keypad system UI polish, outer screen v2, games | dated |
| `ui/` | KEYPAD, KEYPAD-NAV, KEITAI-UI/APPS/MATERIAL, NATIVE-SOFTKEYS, ICONS, secondary (outer) screen | design and behaviour notes, mostly current |
| `ui/HOME-APP-MANAGEMENT.md` | Launcher hiding/restoring apps, keypad paging and move controls | build-tested; deployment pending |
| `ui/KAWAII-SETUP-KEYGUARD.md` | Kawaii first-boot flow, physical SIM PIN entry and quiet unlock hint | source staged; hardware checks pending |
| `radio/` | RADIO, MODEM-* status, firmware analysis, RIL fixes, LTE report | current through 2026-10-11 |
| `hardware/` | Camera, GPU/tearing, FeliCa, TV tuner, microG, root (Magisk) | per-component status |
| `kernel/` | Kernel port assessment, hardening, performance hand-off | research |
| `recovery/` | USB download-mode recovery runbook, stock restore, keitai recovery, recovery tooling | runbook is current |
| `releases/` | RELEASE-v18 … v23 notes | per release |
| `history/` | Old hand-offs, agent briefing, Oreo/Android 8 bring-up and early status notes | historical, may contradict the current state |

Artifacts and evidence stay in `../kyf37-rom/` (release candidates, installer ZIPs, validation JSON, ported-app folders) and `../device-inspection/` (scripts). Superseded files were moved to `../archive/` (manifest `archive/MANIFEST-20261011.tsv`).
