from pathlib import Path
import subprocess, json
root=Path(__file__).resolve().parent.parent
adb=r'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe'
r=json.loads((root/'phone-backup/stream-shift-location.json').read_text())
block=r['last_unshifted_block']
command=f'su -c "/data/local/tmp/kyf37-bootpatch/busybox dd if=/dev/block/mmcblk0p15 bs=4096 skip={block} count=2 2>/dev/null"'
result=subprocess.run([adb,'exec-out',command],capture_output=True,timeout=20)
d=result.stdout
assert result.returncode==0 and len(d)==8192
offset=r['system_disk_offset']+block*4096
with (root/'phone-backup/mmcblk0-live.img.partial').open('rb') as f:
    f.seek(offset)
    a=f.read(8192+47)
i=next(n for n,(x,y) in enumerate(zip(a,d)) if x!=y)
removed=a[i:i+47]
out={'insertion_offset':offset+i,'extra_bytes_hex':removed.hex(),
     'extra_bytes_text':removed.decode(errors='replace'),
     'local_window_matches_after_removing47':a[:i]+a[i+47:]==d}
(root/'phone-backup/stream-insertion-evidence.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
