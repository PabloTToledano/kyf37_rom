from pathlib import Path
import subprocess,json,time,shutil
root=Path('/home/pablo/kyf37-rom/stock-system');out=Path('/home/pablo/kyf37-rom/deoptimized-apps');out.mkdir(exist_ok=True)
java='/home/pablo/kyf37-host-tools/jdk8/bin/java';tool='/home/pablo/kyf37-rom/tools/oat2dex.jar';boot=root/'framework/arm/boot.oat-dex'
results=json.loads((out/'results.json').read_text()) if (out/'results.json').exists() else []
done={x['apk'] for x in results if x['success']}
for base in ['app','priv-app','vendor/app','vendor/priv-app']:
 for apk in sorted((root/base).rglob('*.apk')):
  if str(apk.relative_to(root)) in done:continue
  odex=list(apk.parent.rglob('*.odex'))
  if not odex:continue
  dest=out/apk.relative_to(root).parent;dest.mkdir(parents=True,exist_ok=True)
  command=[java,'-Xmx2g','-jar',tool,str(odex[0]),str(boot)]
  p=subprocess.run(command,capture_output=True,text=True)
  (dest/'deoptimization.log').write_text(p.stdout+p.stderr)
  dexdir=odex[0].parent/(odex[0].name+'-dex');dex=list(dexdir.glob('*.dex'))
  for d in dex:shutil.copy2(d,dest/d.name)
  r={'apk':str(apk.relative_to(root)),'exit_code':p.returncode,'dex_files':[str(d) for d in dex],'warnings':p.stderr,'success':p.returncode==0 and bool(dex)};results.append(r)
  (out/'results.json').write_text(json.dumps(results,indent=2))
  print(r['apk'],r['success'],flush=True)
print('Done',len(results),sum(x['success'] for x in results))
