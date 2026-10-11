#!/usr/bin/env python3
"""Reject stale outer-screen APK media before packaging a ROM. Offline only."""
from pathlib import Path
import argparse
import gzip
import json
import zipfile

workspace = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--apk', type=Path, required=True)
args = parser.parse_args()
media = workspace / 'third-party/bad-apple'
metadata = json.loads((media / 'provenance.json').read_text())
assert metadata['framing']['minimum_width'] >= 80
assert metadata['framing']['maximum_width'] == 128
assert metadata['framing']['full_width_frames'] > 0
frames = (media / 'assets/badapple.frames.gz').read_bytes()
assert len(gzip.decompress(frames)) == metadata['frames'] * 576
with zipfile.ZipFile(args.apk) as apk:
    for name in ('badapple.frames.gz', 'badapple.m4a'):
        assert apk.read('assets/' + name) == (media / 'assets' / name).read_bytes(), \
            'Stale or missing outer-screen asset: ' + name
    assert apk.getinfo('assets/badapple.m4a').compress_type == zipfile.ZIP_STORED, \
        'MediaPlayer openFd requires uncompressed music'
print('Outer release assets verified: adaptive 80–128px video and playable music')
