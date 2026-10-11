"""Check all rewritten helper calls resolve to real assembled method descriptors."""
from pathlib import Path
import re,json,zipfile,subprocess
r=Path('/home/pablo/kyf37-rom');stage=r/'stock-dialer-port';smali=stage/'smali'
available={}
for folder in [smali,r/'kyocera-compat-stage']:
 for p in folder.rglob('*.smali'):
  text=p.read_text();owner=re.search(r'^\.class[^\n]* (L[^;]+;)',text,re.M)
  if owner:available[owner[1]]=set(re.findall(r'^\.method[^\n]*? ([^\s]+\([^\n]+)',text,re.M))
missing=[];checked=0
for p in smali.rglob('*.smali'):
 for owner,method in re.findall(r'invoke-static(?:/range)? \{[^}]*\}, (L(?:org/kyf37/compat|jp/kyocera/kcfp/util/Kyf37)[^;]*;)->([^\s]+)',p.read_text()):
  checked+=1
  if method not in available.get(owner,set()):missing.append({'source':str(p.relative_to(smali)),'owner':owner,'method':method})
# Java compiles against declarations only; verify them against the actual shipped
# stock Guide classes, including every nested helper call in the renderer.
for p in (r/'kyocera-compat-stage/jp/kyocera/kcfp/util').glob('Kyf37*.smali'):
 for owner,method in re.findall(r'invoke-\S+ \{[^}]*\}, (Ljp/kyocera/kcfp/util/KCfpSoftkeyGuide[^;]*;)->([^\s]+)',p.read_text()):
  checked+=1
  if method not in available.get(owner,set()):missing.append({'source':p.name,'owner':owner,'method':method})
tree=Path('/home/pablo/kyf37-android10')
manifest=subprocess.check_output([str(tree/'out/host/linux-x86/bin/aapt2'),'dump','xmltree','--file','AndroidManifest.xml',str(stage/'Kyf37StockDialer.apk')],text=True)
assert 'org.kyf37.compat.CallMemoActivity' in manifest
assert 'android.permission.RECORD_AUDIO' in manifest and 'android.permission.CAPTURE_AUDIO_OUTPUT' in manifest
report={'checked_static_helper_calls':checked,'missing_helpers':missing,'memo_activity_and_permissions_present':True,'hardware_verified':False}
out=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/stock-dialer-port/migration-audit.json');out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert not missing
