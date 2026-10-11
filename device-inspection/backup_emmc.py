"""Stream a live, complete eMMC user-area image to the PC without staging on phone."""
import hashlib
import json
import pathlib
import subprocess
import time

root = pathlib.Path(__file__).resolve().parent.parent
target = root / 'phone-backup' / 'mmcblk0-live.img.partial'
final = target.with_suffix('')
expected = 7634944 * 1024
adb = r'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe'
if target.exists() or final.exists():
    raise SystemExit('Existing image found; refusing to overwrite or restart a backup')
digest = hashlib.sha256()
started = time.monotonic()
total = 0
last_report = 0
with (root / 'phone-backup' / 'emmc-copy-stderr.txt').open('wb') as errors:
    process = subprocess.Popen([adb, 'exec-out', 'su', '-c', 'cat /dev/block/mmcblk0'], stdout=subprocess.PIPE, stderr=errors)
    print(json.dumps({'process_id': process.pid, 'expected_bytes': expected, 'target': str(target)}), flush=True)
    with target.open('xb') as output:
        while chunk := process.stdout.read(1024 * 1024):
            if total == 0 and (chunk[510:512] != b'\x55\xaa' or chunk[512:520] != b'EFI PART'):
                process.terminate()
                raise RuntimeError('Stream does not begin with expected MBR/GPT; refusing invalid image')
            output.write(chunk)
            digest.update(chunk)
            total += len(chunk)
            if total > expected:
                process.terminate()
                raise RuntimeError('Stream exceeds device size')
            if time.monotonic() - last_report > 30:
                last_report = time.monotonic()
                print(json.dumps({'bytes': total, 'percent': round(total / expected * 100, 2), 'elapsed_seconds': round(time.monotonic() - started)}), flush=True)
    result = process.wait()
if result != 0 or total != expected:
    raise RuntimeError(f'Incomplete backup: status={result}, bytes={total}, expected={expected}')
target.rename(final)
manifest = {'path': str(final), 'bytes': total, 'sha256': digest.hexdigest(), 'scope': 'complete eMMC user area; excludes hardware RPMB', 'consistency': 'live image of mounted filesystems; not a guaranteed consistent offline snapshot', 'root_state': 'diagnostic mode and permissive flag enabled; runtime Magisk daemon and su overlay active'}
(root / 'phone-backup' / 'mmcblk0-live-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest), flush=True)
