"""Verify local stock restore sources and compress the system for USB transfer."""
from pathlib import Path
import gzip,hashlib,json
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
source=root/'device-inspection/system-stock.img'
boot=root/'phone-backup/pre-rom-20261007/boot.img'
assert source.stat().st_size==1612709888 and boot.stat().st_size==16777216
assert hashlib.sha256(boot.read_bytes()).hexdigest()=='466fd5ead33dabb54446ecf2f2132edc821e8d7da0c2f5d9f61fb08c45bcc3ed'
destination=Path('/home/pablo/kyf37-rom/system-stock-recovery-20261007.img.gz')
assert not destination.exists()
h=hashlib.sha256()
with source.open('rb') as f,destination.open('wb') as out,gzip.GzipFile(fileobj=out,mode='wb',compresslevel=1,mtime=0) as zipped:
    for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block);zipped.write(block)
assert h.hexdigest()=='76bbf8b49dffd8118f6c7cb8e15559aa1fee2e167a7ce31728239201c14c6f01'
report={'raw_source':str(source),'raw_sha256':h.hexdigest(),'compressed':str(destination),'compressed_bytes':destination.stat().st_size,'boot_sha256':hashlib.sha256(boot.read_bytes()).hexdigest()}
(root/'kyf37-rom/stock-recovery-payload.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
