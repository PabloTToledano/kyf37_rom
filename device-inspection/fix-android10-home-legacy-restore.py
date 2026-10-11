#!/usr/bin/env python3
"""Idempotent: reset the tree's Home.java to the legacy source (Kyf37Home.java.txt) so the older Home patch scripts see the
structure they expect; fix-android10-home-redesign.py then installs the redesigned Home at the end of the chain."""
import pathlib
WS = pathlib.Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
src = (WS / 'device-inspection/Kyf37Home.java.txt').read_text()
dst = pathlib.Path.home() / 'kyf37-android10/packages/apps/Kyf37Home/src/org/kyf37/home/Home.java'
if dst.exists() and dst.read_text() != src:
    dst.write_text(src, newline='\n'); print('Home.java reset to legacy source')
