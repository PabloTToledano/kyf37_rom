from pathlib import Path
import hashlib,json,shutil,subprocess
base=Path('/home/pablo/kyf37-rom')
reference=base/'android10-selinux-reference'
target=base/'kernel-android10'
report=json.loads((reference/'provenance.json').read_text())
for relative,metadata in report['files'].items():
 source=reference/relative
 assert hashlib.sha256(source.read_bytes()).hexdigest()==metadata['sha256']
 destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(source,destination)
report['applied']=True
(reference/'provenance.json').write_text(json.dumps(report,indent=2))
patch=subprocess.check_output(['git','-C',str(target),'diff','--binary'])
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
(host/'kernel-android10-backports.patch').write_bytes(patch)
print('Applied verified SELinux v30 sources only to isolated KYF37 kernel')
