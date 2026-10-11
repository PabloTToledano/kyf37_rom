"""Stage the v10 candidate folder from validated outputs (run in WSL)."""
from pathlib import Path
import shutil, json, hashlib, sys
ws=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms'); reports=ws/'kyf37-rom'
name=sys.argv[1]; boot=Path(sys.argv[2]); raw=Path(sys.argv[3])
folder=reports/('android10-go-candidate-20261007-'+name); folder.mkdir(exist_ok=True)
val=json.loads((reports/'android10-image-validation.json').read_text())
assert val['filesystem_check_exit']==0 and val['raw_system']['path']==str(raw) and val['boot']['path']==str(boot)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()
for src,dst,want in [(boot,'boot-android10-unsigned.img',val['boot']['sha256']),(raw,'system-android10.raw.img',val['raw_system']['sha256']),
                     (Path(val['sparse_system']['path']),'system-android10.sparse.img',val['sparse_system']['sha256'])]:
    shutil.copyfile(src,folder/dst); assert sha(folder/dst)==want,dst
for n in ['android10-image-validation.json','android10-boot-verification.json','android10-system-sparse-verification.json','android10-e2fsck.txt','android10-filesystem-header.txt']:
    shutil.copy2(reports/n,folder/n)
audit_path=reports/('android10-installed-vendor-symbol-audit-'+name+'.json')
audit=json.loads(audit_path.read_text())
assert audit['target']==name and audit['files'], 'Vendor audit must match this revision'
assert not any(x['missing_libraries'] or x['unresolved_strong_symbols'] for x in audit['files']), 'Unresolved vendor symbols block release'
shutil.copy2(audit_path,folder/'android10-installed-vendor-symbol-audit.json')
shutil.copy2(reports/'android10-v9-kernel-module-audit.json',folder/'android10-kernel-module-audit.json')
print(folder)
