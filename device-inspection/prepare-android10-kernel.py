"""Isolate KYF37 source and fetch a pinned same-generation SELinux backport."""
from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,urllib.request
base=Path('/home/pablo/kyf37-rom')
source=base/'kernel-oreo'
target=base/'kernel-android10'
if not target.exists():
 commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
 subprocess.run(['git','-C',str(source),'worktree','add','--detach',str(target),commit],check=True)
 patch=subprocess.check_output(['git','-C',str(source),'diff','--binary'])
 subprocess.run(['git','-C',str(target),'apply','-'],input=patch,check=True)
 # Binder's extra included header/trace are untracked in the earlier worktree.
 for path in source.glob('drivers/staging/android/*'):
  if path.is_file() and not (target/path.relative_to(source)).exists():
   (target/path.relative_to(source)).write_bytes(path.read_bytes())
reference='ccff8f0ae7be1a4b74d118faeed98453fedde8ad'
repo='LineageOS/android_kernel_motorola_msm8916'
headers={'User-Agent':'KYF37-offline-kernel-port'}
def api(path):
 return json.load(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/'+repo+'/git/trees/'+path,headers=headers),timeout=45))
root=api(reference)
security=api(next(x['sha'] for x in root['tree'] if x['path']=='security'))
selinux_sha=next(x['sha'] for x in security['tree'] if x['path']=='selinux')
selinux=api(selinux_sha+'?recursive=1')
assert not selinux.get('truncated')
paths=['security/selinux/'+x['path'] for x in selinux['tree'] if x['type']=='blob']
paths+=['include/linux/lsm_audit.h','security/lsm_audit.c']
reference_root=base/'android10-selinux-reference'
def fetch(path):
 url=f'https://raw.githubusercontent.com/{repo}/{reference}/{path}'
 data=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45).read()
 dest=reference_root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 return path,{'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'url':url}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: files=dict(pool.map(fetch,paths))
report={'repository':repo,'commit':reference,'selinux_tree':selinux_sha,'files':files,'applied':False}
(reference_root/'provenance.json').write_text(json.dumps(report,indent=2))
print('Isolated kernel:',target,'SELinux reference files:',len(files),'not yet applied')
