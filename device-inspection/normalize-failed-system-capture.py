"""Retain dd's appended exec-out status separately after verifying raw bytes."""
from pathlib import Path
import hashlib,json
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
folder=root/'phone-backup/android10-bootloop-20261007'
raw=folder/'system-live.raw.img'
size=1612709888
assert size<raw.stat().st_size<=size+512
h=hashlib.sha256()
with raw.open('rb') as f:
    remaining=size
    while remaining:
        block=f.read(min(4*1024*1024,remaining));assert block
        h.update(block);remaining-=len(block)
    footer=f.read()
assert h.hexdigest()=='c57ec07da96f8ecb77aad7fe860e551dc4565374c1ae2996ed1bd66f15383803'
assert footer.startswith(b'1538+0 records in\n1538+0 records out\n1612709888 bytes')
(folder/'capture-dd-footer.txt').write_bytes(footer)
with raw.open('r+b') as f:f.truncate(size)
report={'path':str(raw),'bytes':size,'sha256':h.hexdigest(),
        'phone_read_only':True,'raw_matches_independent_live_partition_hash':True,
        'appended_dd_status_retained_separately':True}
(folder/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
