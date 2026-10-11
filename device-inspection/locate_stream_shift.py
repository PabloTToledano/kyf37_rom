"""Compare immutable system blocks to locate the backup's observed byte shift."""
import json, subprocess
from pathlib import Path
root = Path(__file__).resolve().parent.parent
adb = r'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe'
mapping = json.loads((root/'phone-backup/partition-map.json').read_text())
system = next(p for p in mapping['partitions'] if p['name']=='system')
image = Path(mapping['source'])
records = []
def classify(block):
    command = f'su -c "/data/local/tmp/kyf37-bootpatch/busybox dd if=/dev/block/mmcblk0p15 bs=4096 skip={block} count=1 2>/dev/null"'
    result = subprocess.run([adb, 'exec-out', command], capture_output=True, timeout=20)
    assert result.returncode == 0 and len(result.stdout)==4096, (result.returncode,len(result.stdout),result.stderr)
    with image.open('rb') as f:
        offset = system['offset_bytes']+block*4096
        f.seek(offset)
        sample = f.read(4096+47)
    exact = sample[:4096] == result.stdout
    shifted = sample[47:47+4096] == result.stdout
    records.append({'block':block,'exact':exact,'shifted47':shifted})
    print(json.dumps(records[-1]),flush=True)
    return 0 if exact and not shifted else 47 if shifted and not exact else None
lo,hi=0,system['bytes']//4096-1
assert classify(lo)==0
# Skip sparse zero tail locally, without hundreds of phone transactions.
with image.open('rb') as f:
    while hi>lo:
        f.seek(system['offset_bytes']+hi*4096)
        if any(f.read(4096)):
            break
        hi-=1
assert classify(hi)==47
while hi-lo>1:
    mid=(hi+lo)//2
    # Find nearby informative bytes locally; all-zero samples hide a shift.
    with image.open('rb') as f:
        candidates = []
        for direction in (1,-1):
            candidate=mid
            while lo<candidate<hi:
                f.seek(system['offset_bytes']+candidate*4096)
                if any(f.read(4096+47)):
                    candidates.append(candidate)
                    break
                candidate+=direction
        if not candidates:break
        mid=min(candidates,key=lambda n:abs(n-mid))
    state=classify(mid)
    if state is None:
        # Sparse all-zero blocks cannot establish a shift. Probe nearby blocks.
        for delta in range(1,4):
            if mid+delta>=hi:break
            state=classify(mid+delta)
            if state is not None:
                mid+=delta
                break
    if state is None:break
    if state==0:lo=mid
    else:hi=mid
report={'last_unshifted_block':lo,'first_shifted_block':hi,'system_disk_offset':system['offset_bytes'],'samples':records}
(root/'phone-backup/stream-shift-location.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='samples'}))
