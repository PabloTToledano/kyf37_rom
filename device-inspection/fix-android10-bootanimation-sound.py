#!/usr/bin/env python3
"""Add Movistar sound effect to KYF37 Kirby boot animation in Android 10 source tree.

Normalizes the input WAV file headers to standard 16-bit stereo 48000Hz PCM,
packs part0/audio.wav into bootanimation.zip using ZIP_STORED (0% compression),
and ensures persist.sys.bootanim.play_sound=1 in device.mk.
Idempotent; runs under WSL or Windows Python.
"""
from pathlib import Path
import struct
import io
import wave
import zipfile
import hashlib
import sys

# Locate workspaces / paths whether run under WSL or Windows
wsl_tree = Path('/home/pablo/kyf37-android10')
win_tree = Path(r'\\wsl$\Ubuntu\home\pablo\kyf37-android10')
tree = wsl_tree if wsl_tree.exists() else win_tree

wsl_dl = Path('/mnt/c/Users/pablo/Downloads')
win_dl = Path(r'C:\Users\pablo\Downloads')
dl = wsl_dl if wsl_dl.exists() else win_dl

wav_file = dl / 'Tono_de_llamada_movistar_oficial.wav'
assert wav_file.is_file(), f"WAV file not found: {wav_file}"

bootanim_source = tree / 'device/kyocera/kyf37/bootanimation.zip'
if not bootanim_source.is_file():
    bootanim_source = dl / 'bootanimation.zip'
assert bootanim_source.is_file(), f"Boot animation zip not found: {bootanim_source}"

print(f"Reading sound effect from {wav_file}...")
raw_bytes = wav_file.read_bytes()

# Extract PCM samples after 'data' chunk header
data_idx = raw_bytes.find(b'data')
assert data_idx != -1, "No data chunk found in WAV file"
pcm_data = raw_bytes[data_idx + 8:]
pcm_len = len(pcm_data)
assert pcm_len > 0, "No audio samples found"

# Construct standard RIFF/WAVE PCM 16-bit stereo 48000Hz header
riff_sz = 36 + pcm_len
clean_header = struct.pack(
    '<4sI4s4sIHHIIHH4sI',
    b'RIFF', riff_sz, b'WAVE',
    b'fmt ', 16, 1, 2, 48000, 192000, 4, 16,
    b'data', pcm_len
)
clean_wav = clean_header + pcm_data

# Validate reconstructed WAV with wave module
with wave.open(io.BytesIO(clean_wav), 'rb') as w:
    nchannels = w.getnchannels()
    sampwidth = w.getsampwidth()
    framerate = w.getframerate()
    nframes = w.getnframes()
    duration = nframes / framerate
    assert nchannels == 2, f"Expected 2 channels, got {nchannels}"
    assert sampwidth == 2, f"Expected 16-bit width (2), got {sampwidth}"
    assert framerate == 48000, f"Expected 48000Hz, got {framerate}"
    print(f"Clean WAV: {nchannels}ch, {sampwidth*8}bit, {framerate}Hz, {nframes} frames, {duration:.2f}s ({len(clean_wav)} bytes)")

# Read existing bootanimation.zip entries
print(f"Reading bootanimation from {bootanim_source}...")
new_zip_buffer = io.BytesIO()
with zipfile.ZipFile(bootanim_source, 'r') as zin:
    with zipfile.ZipFile(new_zip_buffer, 'w', compression=zipfile.ZIP_STORED) as zout:
        for item in zin.infolist():
            if item.filename in ('part0/audio.wav', 'audio.wav'):
                continue
            data = zin.read(item.filename)
            zinfo = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            zinfo.compress_type = zipfile.ZIP_STORED
            zout.writestr(zinfo, data)
        # Add part0/audio.wav (uncompressed)
        ainfo = zipfile.ZipInfo(filename='part0/audio.wav', date_time=(2026, 10, 8, 21, 30, 0))
        ainfo.compress_type = zipfile.ZIP_STORED
        zout.writestr(ainfo, clean_wav)

new_zip_bytes = new_zip_buffer.getvalue()
new_zip_sha256 = hashlib.sha256(new_zip_bytes).hexdigest()

# Validate that ALL entries are stored without compression
with zipfile.ZipFile(io.BytesIO(new_zip_bytes), 'r') as zcheck:
    items = zcheck.infolist()
    filenames = [z.filename for z in items]
    assert 'desc.txt' in filenames, "desc.txt missing from zip"
    assert 'part0/audio.wav' in filenames, "part0/audio.wav missing from zip"
    for z in items:
        assert z.compress_type == zipfile.ZIP_STORED, f"Entry {z.filename} is not ZIP_STORED ({z.compress_type})"
    print(f"Zip verified: {len(items)} entries, ALL uncompressed (STORED), total size {len(new_zip_bytes)} bytes")
    print(f"New bootanimation.zip SHA-256: {new_zip_sha256}")

# Write updated zip to targets
targets = [
    tree / 'device/kyocera/kyf37/bootanimation.zip',
    dl / 'bootanimation.zip',
]
out_bootanim = tree / 'out/target/product/kyf37/system/media/bootanimation.zip'
if out_bootanim.parent.exists():
    targets.append(out_bootanim)

for target in targets:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(new_zip_bytes)
    print(f"Updated {target}")

# Also update extracted folder in Downloads if present
unpacked_dir = dl / 'bootanimation/part0'
if unpacked_dir.exists():
    (unpacked_dir / 'audio.wav').write_bytes(clean_wav)
    print(f"Updated {unpacked_dir / 'audio.wav'}")

# Ensure persist.sys.bootanim.play_sound=1 in device.mk
device_mk = tree / 'device/kyocera/kyf37/device.mk'
if device_mk.is_file():
    content = device_mk.read_text()
    if 'persist.sys.bootanim.play_sound' not in content:
        content += '\nPRODUCT_PROPERTY_OVERRIDES += persist.sys.bootanim.play_sound=1\n'
        device_mk.write_text(content)
        print(f"Added persist.sys.bootanim.play_sound=1 to {device_mk}")
    else:
        print(f"persist.sys.bootanim.play_sound already present in {device_mk}")

print("Boot animation sound integration complete and verified.")
