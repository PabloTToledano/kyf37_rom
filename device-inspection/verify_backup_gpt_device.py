from pathlib import Path
import subprocess,hashlib,json
root=Path(__file__).resolve().parent.parent
adb=r'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe'
image=root/'phone-backup/mmcblk0-corrected.img.partial'
records=[]
with image.open('rb') as f:
    for start,count in [(0,34),(15269855,33)]:
        cmd=f'su -c "/data/local/tmp/kyf37-bootpatch/busybox dd if=/dev/block/mmcblk0 bs=512 skip={start} count={count} 2>/dev/null"'
        r=subprocess.run([adb,'exec-out',cmd],capture_output=True,timeout=20)
        assert r.returncode==0 and len(r.stdout)==count*512
        f.seek(start*512)
        local=f.read(count*512)
        records.append({'start_lba':start,'bytes':len(local),'matches_phone':local==r.stdout,
                        'sha256':hashlib.sha256(local).hexdigest()})
assert all(r['matches_phone'] for r in records)
(root/'phone-backup/gpt-device-comparison.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
