"""Inventory every owner stock APK and assign explicit port/verification states."""
from pathlib import Path
import subprocess,re,json
tree=Path('/home/pablo/kyf37-android10');r=Path('/home/pablo/kyf37-rom');stock=r/'stock-system';aapt=tree/'out/host/linux-x86/bin/aapt2'
rows=[]
host=Path(__file__).resolve().parent.parent/'kyf37-rom/all-stock-app-ports'
assembled=json.loads((host/'assembly-reports.json').read_text()) if (host/'assembly-reports.json').exists() else []
candidates={x['stock_module'] for x in assembled}
for category in ['app','priv-app']:
 for apk in sorted((stock/category).rglob('*.apk')):
  result=subprocess.run([str(aapt),'dump','badging',str(apk)],capture_output=True,text=True)
  match=re.search(r"package: name='([^']+)'",result.stdout)
  if not match:raise RuntimeError(str(apk)+result.stderr)
  package=match[1];module=apk.parent.name;label=re.search(r"application-label:'([^']*)'",result.stdout)
  launcher=re.search(r"launchable-activity: name='([^']+)'",result.stdout)
  xml=subprocess.check_output([str(aapt),'dump','xmltree','--file','AndroidManifest.xml',str(apk)],text=True)
  shared=re.search(r'sharedUserId[^\n]*?"([^"]+)"',xml)
  libraries=re.findall(r'uses-library\s*.*?(?=\n\s*E:|\Z)',xml,re.S)
  dex=list((r/'deoptimized-apps'/category/module).glob('*.dex'))
  oem=package.startswith(('jp.kyocera.','com.kyocera.'))
  built=list((tree/'out/target/product/kyf37/system').rglob(apk.name))
  if module in ['KyoceraCamera','MemoPad','MemoPadProvider','kc_soundrecorder','kc_soundrecorder_manager','Reader']:
   state='selected-port-built';state='photo-capture-hardware-verified/latest-softkeys-unverified' if module=='KyoceraCamera' else state
  elif module=='MobileLight':state='replaced-by-keypad-flashlight'
  elif module=='Dialer':state='experimental-port/answering-machine-unresolved'
  elif module=='FsDtvApp':state='staged/native-ABI-blocked'
  else:state='not-ported' if oem else 'inventory/review-required'
  if module in candidates and state in ['not-ported','inventory/review-required']:state='candidate-assembled/not-enabled/not-hardware-verified'
  rows.append({'module':module,'category':category,'package':package,'label':label[1] if label else None,'launcher':launcher[1] if launcher else None,'kyocera_package':oem,'bytes':apk.stat().st_size,'stock_apk':str(apk),'deodexed_dex':[str(p) for p in dex],'shared_uid':shared[1] if shared else None,'uses_library_manifest':libraries,'build_output_candidates':[str(p) for p in built],'status':state})
folder=Path(__file__).resolve().parent.parent/'kyf37-rom/all-stock-app-ports';folder.mkdir(exist_ok=True)
(folder/'inventory.json').write_text(json.dumps(rows,indent=2)+'\n')
(folder/'inventory.md').write_text('# Owner stock app inventory\n\nPackage prefixes identify Kyocera apps, not all carrier/OEM-modified apps.\nBuild output presence is not functionality verification.\n\n| Module | Package | State | Dex available |\n|---|---|---|---|\n'+''.join('| '+x['module']+' | '+x['package']+' | '+x['status']+' | '+str(bool(x['deodexed_dex']))+' |\n' for x in rows))
print('Stock APKs:',len(rows),'Kyocera packages:',sum(x['kyocera_package'] for x in rows))
for x in rows:
 if x['kyocera_package']:print(x['module'],x['package'],x['status'],'dex='+str(bool(x['deodexed_dex'])))
