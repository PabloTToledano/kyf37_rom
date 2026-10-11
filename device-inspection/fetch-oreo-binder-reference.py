from pathlib import Path
import urllib.request,json,hashlib

repo='LineageOS/android_kernel_motorola_msm8916'
commit='603472fcb89313369018d61b302b2f5766d6d08f'
out=Path('kyf37-rom/binder-oreo-reference');out.mkdir(exist_ok=True)
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'KYF37-ROM-bringup'})
 with urllib.request.urlopen(req,timeout=60) as r:return r.read()
manifest=[]
for folder in ['drivers/staging/android','drivers/staging/android/uapi','include/uapi/linux/android']:
 try:
  listing=json.loads(get(f'https://api.github.com/repos/{repo}/contents/{folder}?ref={commit}'))
 except urllib.error.HTTPError as e:
  if e.code==404:continue
  raise
 for item in listing:
  name=item['name']
  if item['type']!='file' or not(name.startswith('binder') or name in ['Kconfig','Makefile']):continue
  path=item['path'];data=get(f'https://raw.githubusercontent.com/{repo}/{commit}/{path}')
  dest=out/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  manifest.append({'path':path,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
assert any(x['path'].endswith('/binder.c') for x in manifest)
(out/'provenance.json').write_text(json.dumps({'repository':repo,'commit':commit,
 'files':manifest,'note':'Reference only. No other-device kernel/config/DT/modem images used; compatibility and kernel backport still require review/build.'},indent=2))
print('Pinned Binder reference:',commit,len(manifest),'files')
