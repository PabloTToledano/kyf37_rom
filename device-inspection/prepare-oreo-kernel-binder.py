from pathlib import Path
import subprocess,json,shutil,hashlib

base=Path('/home/pablo/kyf37-rom/kernel-source')
dest=Path('/home/pablo/kyf37-rom/kernel-oreo')
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
reference=host/'kyf37-rom/binder-oreo-reference'
if not dest.exists():
 subprocess.run(['git','-C',str(base),'worktree','add','--detach',str(dest),
  '57a11bec679273e797cbf3fcb3fc1488637b3fe6'],check=True)
assert subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()=='57a11bec679273e797cbf3fcb3fc1488637b3fe6'
provenance=json.loads((reference/'provenance.json').read_text())
for item in provenance['files']:
 rel=item['path']
 if '/binder' not in rel:continue
 assert rel.startswith('drivers/staging/android/')
 data=(reference/rel).read_bytes()
 assert hashlib.sha256(data).hexdigest()==item['sha256']
 p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
p=dest/'drivers/staging/android/Kconfig'
s=p.read_text()
if 'config ANDROID_BINDER_DEVICES' not in s:
 upstream=(reference/'drivers/staging/android/Kconfig').read_text()
 block=upstream.split('config ANDROID_BINDER_DEVICES\n',1)[1].split('\nconfig ',1)[0]
 marker='config ASHMEM\n'
 assert s.count(marker)==1
 s=s.replace(marker,'config ANDROID_BINDER_DEVICES\n'+block+'\n'+marker,1)
 p.write_text(s)
p=dest/'arch/arm/configs/KYF37_defconfig'
s=p.read_text()
assert 'CONFIG_ANDROID_BINDER_IPC_32BIT=y' in s
if 'CONFIG_ANDROID_BINDER_DEVICES=' not in s:
 p.write_text(s+'\nCONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"\n')
patch=subprocess.check_output(['git','-C',str(dest),'diff','--binary'])
(host/'kyf37-rom/kernel-binder-oreo.patch').write_bytes(patch)
print('Staged Binder-only backport on isolated KYF37 kernel; no boot image changed')
