from pathlib import Path
import hashlib
import json
import zipfile

r = Path('/home/pablo/kyf37-android10')
files = [
    Path('/mnt/c/Users/pablo/Downloads/bootanimation.zip'),
    r / 'device/kyocera/kyf37/bootanimation.zip',
    r / 'out/target/product/kyf37/system/media/bootanimation.zip',
]
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
print(json.dumps(hashes, indent=2))
assert len(set(hashes.values())) == 1, "Hashes do not match across bootanimation targets!"

# Verify audio.wav is present and STORED (0 compression) in each file
for p in files:
    if not p.is_file():
        continue
    with zipfile.ZipFile(p, 'r') as zf:
        names = zf.namelist()
        assert 'part0/audio.wav' in names, f"part0/audio.wav missing from {p}"
        info = zf.getinfo('part0/audio.wav')
        assert info.compress_type == zipfile.ZIP_STORED, f"part0/audio.wav not STORED in {p}"
        for z in zf.infolist():
            assert z.compress_type == zipfile.ZIP_STORED, f"{z.filename} not STORED in {p}"

print("All bootanimation.zip files match and have valid STORED part0/audio.wav.")
