#!/usr/bin/env python3
"""Idempotent: keep non-interactive utility apps (AudioFX equalizer service UI) off the keypad Home grid.
Patches Home.java + Kyf37Home.java.txt after the hideLegacy() calls (see fix-android10-keitai-apps.py). Run in WSL."""
import pathlib
WS = pathlib.Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
HIDE = ['org.lineageos.audiofx']
anchor = '        hideLegacy(pm, seen, "org.kyf37.contacts", "com.android.contacts");\n'
add = ''.join('        seen.add("%s"); // utility app, not useful on the keypad grid\n' % p for p in HIDE)
for f in [pathlib.Path.home() / 'kyf37-android10/packages/apps/Kyf37Home/src/org/kyf37/home/Home.java', WS / 'device-inspection/Kyf37Home.java.txt']:
    if not f.exists(): continue
    t = f.read_text()
    if add in t: print('already', f); continue
    if anchor not in t: print('WARN anchor missing', f); continue
    f.write_text(t.replace(anchor, anchor + add, 1), newline='\n'); print('patched', f)
