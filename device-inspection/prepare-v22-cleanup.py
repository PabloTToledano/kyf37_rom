"""Plan file-only retirement after a verified v22 ZIP; keep v19/v20 ZIP rollback."""
from pathlib import Path
import hashlib, json, re, zipfile
root = Path(__file__).resolve().parent.parent
rom = root/'kyf37-rom'
report = json.loads((rom/'v22-validation.json').read_text())
assert report['zip_crc_and_payload_hashes_verified']
assert report['revision'] == 'v22'
def digest(f):
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(8<<20), b''): h.update(chunk)
    return h.hexdigest()
with Path(report['zip']).open('rb') as f:
    assert digest(f) == report['sha256']
files = []
def add(p, reason):
    if p.is_file():
        files.append({'path':str(p.relative_to(root)), 'bytes':p.stat().st_size, 'reason':reason})
# Verify the retained rollback installers before discarding staging duplicates.
for revision in ('v19', 'v20'):
    p = rom/f'kyf37-android10-go-20261007-twrp-{revision}.zip'
    with zipfile.ZipFile(p) as z:
        manifest = json.loads(z.read('payload-manifest.json'))
        for name in ('boot.img', 'system.raw.img'):
            with z.open(name) as f: assert digest(f) == manifest[name]['sha256']
    folder = rom/f'android10-go-candidate-20261007-{revision}'
    raw = folder/'system-android10.raw.img'
    if raw.exists():
        with raw.open('rb') as f: assert digest(f) == manifest['system.raw.img']['sha256']
    for name in ('system-android10.raw.img', 'system-android10.sparse.img'):
        add(folder/name, 'Regenerable staging image; verified matching release ZIP retained')
for p in rom.glob('kyf37-android10-go-20261007-twrp-v*.zip'):
    match = re.fullmatch(r'kyf37-android10-go-20261007-twrp-v(\d+)\.zip', p.name)
    if match and int(match[1]) <= 18:
        add(p, 'Obsolete pre-v19 installer; v19/v20 rollback and validated v22 retained')
        add(p.with_suffix('.zip.sha256'), 'Checksum of retired installer')
for p in (rom/'systemui-loop/apk').glob('SystemUI-*.apk'):
    if re.fullmatch(r'SystemUI-(?:iter[1-8]|m[1-7])\.apk', p.name):
        add(p, 'Superseded SystemUI test iteration; original rollback, m8 and current release retained')
retired = []
for folder in rom.glob('android10-go-candidate-20261007-v*'):
    match = re.fullmatch(r'android10-go-candidate-20261007-v(\d+)', folder.name)
    if match and int(match[1]) <= 18:
        retired.extend(p for p in folder.rglob('*') if p.is_file())
history = rom/'retired-release-metadata-20261011.zip'
if not history.exists():
    with zipfile.ZipFile(history, 'w', zipfile.ZIP_DEFLATED) as z:
        manifest = {}
        for p in retired:
            if p.suffix == '.img': continue
            name = p.relative_to(root).as_posix()
            data = p.read_bytes()
            manifest[name] = hashlib.sha256(data).hexdigest()
            z.writestr(name, data)
        z.writestr('manifest.json', json.dumps(manifest, indent=2))
with zipfile.ZipFile(history) as z:
    assert z.testzip() is None
    manifest = json.loads(z.read('manifest.json'))
    for name, want in manifest.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == want
        p = root/name
        if p.exists():
            with p.open('rb') as f: assert digest(f) == want
for p in retired:
    add(p, 'Retired pre-v19 staging artifact; metadata checksummed in history archive, v19/v20 rollback retained')
add(rom/'system-lineage-final.img', 'Obsolete Android 7 experimental system image; no current build-script consumers, stock and Android 10 rollback retained')
(root/'device-inspection/cleanup-plan-v22.json').write_text(json.dumps({'root':str(root), 'files':files, 'total_bytes':sum(f['bytes'] for f in files)}, indent=2))
print('Planned', len(files), 'files;', round(sum(f['bytes'] for f in files)/1024**3,2), 'GiB')
