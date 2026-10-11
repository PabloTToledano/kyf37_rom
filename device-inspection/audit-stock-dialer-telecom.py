"""Check declared Telecom method descriptors used by the OEM dialer."""
from pathlib import Path
import re,subprocess,json
r=Path('/home/pablo/kyf37-rom');root=Path('/home/pablo/kyf37-android10');stage=r/'stock-dialer-port'
needed={}
for p in (stage/'smali/com/android/incallui').rglob('*.smali'):
 for owner,name,desc in re.findall(r'invoke-\S+ \{[^}]*\}, L(android/telecom/[^;]+);->([^\(]+)(\([^\n\s]+)',p.read_text()):
  needed.setdefault(owner,set()).add((name,desc))
missing={};cp=root/'out/target/common/obj/JAVA_LIBRARIES/framework_intermediates/classes.jar'
for owner,refs in needed.items():
 proc=subprocess.run(['/home/pablo/kyf37-host-tools/jdk8/bin/javap','-p','-s','-classpath',str(cp),owner.replace('/','.')],capture_output=True,text=True)
 if proc.returncode:continue # Bundled legacy class: class audit covers this separately.
 lines=proc.stdout.splitlines();have=set()
 for i,line in enumerate(lines):
  m=re.search(r'descriptor: (\(.*)',line)
  if m and i:
   n=re.search(r'([^\s.(]+)\(',lines[i-1])
   if n:have.add((n[1],m[1].strip()))
 absent=sorted(name+desc for name,desc in refs if name!='<init>' and (name,desc) not in have)
 if absent:missing[owner]=absent
report={'missing_declared_telecom_methods':missing,'scope':'Declared Android 10 method descriptors; inherited methods require manual review. Not a call-behavior test.'}
for folder in [stage,Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/stock-dialer-port')]:
 (folder/'telecom-method-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
