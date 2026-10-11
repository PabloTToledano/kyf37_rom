#!/usr/bin/env python3
"""Drive the host-test TWRP (qemu-arm, fake framebuffer) with D-pad key events and capture frames.

Runs inside WSL (stdlib only). Usage:
    python3 hosttest-drive.py scenario.json OUTDIR

scenario.json is a list of steps:
    {"key": "down", "n": 2}        press+release a key (names below or a Linux code), n times
    {"wait": 2.0}                  sleep
    {"shot": "main-menu"}          wait for the screen to settle, copy /fb.raw to OUTDIR/<name>.raw
    {"expect_log": "text"}         assert that /tmp/recovery.log contains text (recorded in results)
The TWRP process must already be running (run-hosttest.sh). Frames are raw RGBX 480x854.
"""
import json
import os
import shutil
import struct
import sys
import time

ROOT = '/home/pablo/kyf37-twrp-hosttest/root'
FIFO = ROOT + '/dev/input/event0'
FB = ROOT + '/fb.raw'
LOG = ROOT + '/tmp/recovery.log'
KEYS = {'up': 103, 'down': 108, 'left': 105, 'right': 106, 'enter': 28, 'ok': 28, 'back': 355, 'clear': 355,
        'f1': 59, 'f2': 60, 'f3': 61, 'f4': 62, 'end': 116, 'side': 254, 'star': 55, 'pound': 253, 'send': 231}
for d in range(1, 10):
    KEYS[str(d)] = 1 + d
KEYS['0'] = 11


class Feeder:
    def __init__(self):
        self.fd = os.open(FIFO, os.O_WRONLY)  # blocks until TWRP opens the read side

    def ev(self, typ, code, val):
        t = time.time()
        os.write(self.fd, struct.pack('<IIHHi', int(t), int((t % 1) * 1e6), typ, code, val))

    def press(self, code, hold=0.12):
        self.ev(1, code, 1)
        self.ev(0, 0, 0)
        time.sleep(hold)
        self.ev(1, code, 0)
        self.ev(0, 0, 0)


def settle(prev_mtime, timeout=6.0, quiet=1.2):
    """Wait until fb.raw changed since prev_mtime and then stayed unchanged for `quiet` seconds."""
    start = time.time()
    last = prev_mtime
    changed_at = None
    while time.time() - start < timeout:
        try:
            m = os.stat(FB).st_mtime_ns
        except OSError:
            m = 0
        if m != last:
            last = m
            changed_at = time.time()
        if changed_at is not None and time.time() - changed_at > quiet:
            break
        time.sleep(0.15)
    return last


def main():
    scen = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    f = Feeder()
    results = []
    mt = os.stat(FB).st_mtime_ns if os.path.exists(FB) else 0
    time.sleep(1.0)
    for st in scen:
        if 'wait' in st:
            time.sleep(st['wait'])
        elif 'key' in st:
            code = KEYS.get(str(st['key']), None)
            if code is None:
                code = int(st['key'])
            for _ in range(st.get('n', 1)):
                f.press(code)
                mt = settle(mt, timeout=st.get('timeout', 4.0), quiet=0.8)
        elif 'shot' in st:
            mt = settle(mt, timeout=2.0, quiet=0.8)
            shutil.copyfile(FB, os.path.join(out, st['shot'] + '.raw'))
            results.append(('shot', st['shot'], os.stat(FB).st_size))
        elif 'expect_log' in st:
            txt = open(LOG, errors='replace').read() if os.path.exists(LOG) else ''
            results.append(('log', st['expect_log'], st['expect_log'] in txt))
    json.dump(results, open(os.path.join(out, 'results.json'), 'w'), indent=1)
    shutil.copyfile(LOG, os.path.join(out, 'recovery.log')) if os.path.exists(LOG) else None
    print(json.dumps(results))


main()
