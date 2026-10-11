from pathlib import Path
import subprocess,json,zipfile,hashlib
root=Path('/home/pablo/kyf37-rom/stock-system')
out=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom');out.mkdir(exist_ok=True)
aapt='/home/pablo/kyf37-twrp/prebuilts/sdk/tools/linux/aapt'
apps=[]
for f in sorted(root.rglob('*.apk')):
 p=subprocess.run([aapt,'dump','badging',str(f)],capture_output=True,text=True)
 x=subprocess.run([aapt,'dump','xmltree',str(f),'AndroidManifest.xml'],capture_output=True,text=True)
 with zipfile.ZipFile(f) as z:
  names=z.namelist();libs=[n for n in names if n.startswith('lib/')]
 apps.append({'path':str(f.relative_to(root)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'has_classes_dex':'classes.dex' in names,'native_libraries':libs,'odex_files':[str(v.relative_to(root)) for v in f.parent.rglob('*.odex')],'badging':p.stdout,'manifest_tree':x.stdout,'parser_errors':p.stderr+x.stderr})
(out/'stock-app-inventory.json').write_text(json.dumps(apps,indent=2))
framework=[]
for f in sorted((root/'framework').glob('*.jar')):
 with zipfile.ZipFile(f) as z: dex='classes.dex' in z.namelist()
 framework.append({'path':str(f.relative_to(root)),'has_classes_dex':dex,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(out/'stock-framework-inventory.json').write_text(json.dumps(framework,indent=2))
print('Apps',len(apps),'without embedded DEX',sum(not a['has_classes_dex'] for a in apps),'framework JARs',len(framework))
