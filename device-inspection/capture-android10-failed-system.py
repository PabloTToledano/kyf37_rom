"""Read-only capture of installed system for offline bootloop diagnosis."""
from pathlib import Path
import subprocess,hashlib,json
root=Path(__file__).resolve().parent.parent
adb=r'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe'
target=root/'phone-backup/android10-bootloop-20261007'
target.mkdir(exist_ok=True)
output=target/'system-live.raw.img'
assert not output.exists()
with output.open('wb') as stream:
    result=subprocess.run([adb,'-s','981108631314','exec-out','/sbin/busybox dd if=/dev/block/bootdevice/by-name/system bs=1048576 2>/tmp/kyf37-system-capture-dd.log'],stdout=stream,stderr=subprocess.PIPE)
assert result.returncode==0,result.stderr.decode(errors='replace')
assert output.stat().st_size==1612709888
h=hashlib.sha256()
with output.open('rb') as stream:
    for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
report={'path':str(output),'bytes':output.stat().st_size,'sha256':h.hexdigest(),'phone_read_only':True}
(target/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
