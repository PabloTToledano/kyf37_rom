"""Archive reviewed ROM outputs and public reports; never include signing keys."""
from pathlib import Path
import json, hashlib, shutil, zipfile
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
folder=root/'kyf37-rom/android10-go-candidate-20261007'
for name in ['android10-spain-qmi-tests.json']:
    shutil.copy2(root/'kyf37-rom'/name,folder/name)
shutil.copy2(root/'KYF37-USB-RECOVERY-RUNBOOK.md',folder/'KYF37-USB-RECOVERY-RUNBOOK.md')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
sign=json.loads((folder/'boot-android10-owner-signed.signing.json').read_text())
assert sign['signature_verified'] and sign['body_preserved']
assert digest(folder/'boot-android10-owner-signed.img')==sign['sha256']
(folder/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(folder.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
destination=folder.parent/'kyf37-android10-go-candidate-20261007-images.zip'
assert not destination.exists(), 'Do not overwrite an existing published candidate'
temporary=destination.with_suffix('.zip.partial')
assert not temporary.exists()
names=[p.name for p in folder.iterdir() if p.is_file() and p.suffix in ('.json','.md','.txt','.xml')]
names+=['SHA256SUMS','boot-android10-owner-signed.img','system-android10.raw.img']
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
    for name in sorted(names): archive.write(folder/name,arcname=name)
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist())==set(names)
temporary.rename(destination)
report={'archive':str(destination),'bytes':destination.stat().st_size,'sha256':digest(destination),
        'zip_crc_verified':True,'automatic_installer':False,
        'hardware_boot_verified':False,'ims_service_port_complete':False,
        'lte_current_mask_verified':False}
(folder.parent/'android10-candidate-bundle.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
