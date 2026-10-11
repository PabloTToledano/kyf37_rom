#!/usr/bin/env python3
"""Idempotent: install the keitai / Material You Home (move-in-grid + folders) from Kyf37HomeRedesign.java.txt over the
tree's Home.java. Must run AFTER every other script that patches Home.java (they only patch anchors of the old file and
WARN harmlessly on the new one). Run in WSL."""
import pathlib
WS = pathlib.Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
src = (WS / 'device-inspection/Kyf37HomeRedesign.java.txt').read_text()
dst = pathlib.Path.home() / 'kyf37-android10/packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
if not dst.exists() or dst.read_text() != src:
    dst.write_text(src, newline='\n'); print('installed redesigned Home.java')
else:
    print('Home.java up to date')
