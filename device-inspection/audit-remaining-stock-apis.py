"""Audit legacy bytecode against current boot classes, resolving inheritance.

Reports unresolved contracts; does not substitute stubs or claim runtime readiness.
"""
from pathlib import Path
import zipfile,subprocess,re,json,hashlib
here=Path(__file__).resolve().parent;ws=here.parent;r=Path('/home/pablo/kyf37-rom');tree=Path('/home/pablo/kyf37-android10');stage=r/'remaining-stock-ports'
jars=[];boot=set()
for module in ['framework','telephony-common','voip-common','ims-common','core-oj','core-libart','ext','org.apache.http.legacy']:
 p=tree/f'out/target/common/obj/JAVA_LIBRARIES/{module}_intermediates/classes.jar'
 if p.exists():jars.append(p)
for p in [tree/f'out/soong/.intermediates/libcore/{m}/android_common/javac/{m}.jar' for m in ['core-oj','core-libart']]:
 if p.exists():jars.append(p)
for p in jars:
 with zipfile.ZipFile(p) as z:boot.update(n[:-6] for n in z.namelist() if n.endswith('.class'))
refs={};owners=set()
for folder in sorted(stage.iterdir()):
 if not (folder/'report.json').exists():continue
 methods=set();fields=set()
 for p in (folder/'smali').rglob('*.smali'):
  text=p.read_text()
  for owner,name,desc in re.findall(r'invoke-\S+ \{[^}]*\}, L([^;]+);->([^\s(]+)(\([^\s]+)',text):
   if owner in boot:methods.add((owner,name,desc));owners.add(owner)
  for owner,name,desc in re.findall(r'(?:iget|iput|sget|sput)\S* [^\n]*?, L([^;]+);->([^:\s]+):([^\s]+)',text):
   if owner in boot:fields.add((owner,name,desc));owners.add(owner)
 refs[folder.name]=(methods,fields)
java=Path('/home/pablo/kyf37-host-tools/jdk8/bin/javap');cp=':'.join(str(p) for p in jars)
key=hashlib.sha256('|'.join(str(p)+':'+str(p.stat().st_mtime_ns)+':'+str(p.stat().st_size) for p in jars).encode()).hexdigest()[:12]
cache=stage/'current-api-cache'/key;cache.mkdir(parents=True,exist_ok=True)
definitions={};queue=list(sorted(owners))
while queue:
 owner=queue.pop()
 if owner in definitions:continue
 file=cache/(owner.replace('/','_')+'.txt')
 # Classpath builds can change: only use cache if newer than every input jar.
 if not file.exists() or any(p.stat().st_mtime>file.stat().st_mtime for p in jars):
  result=subprocess.run([str(java),'-p','-s','-classpath',cp,owner.replace('/','.')],capture_output=True,text=True)
  if result.returncode:definitions[owner]={'methods':set(),'fields':set(),'parents':[],'error':result.stderr};continue
  file.write_text(result.stdout)
 lines=file.read_text().splitlines();methods=set();fields=set();parents=[]
 for i,line in enumerate(lines):
  if ' class ' in line or ' interface ' in line:
   cleaned=line
   while re.search(r'<[^<>]*>',cleaned):cleaned=re.sub(r'<[^<>]*>','',cleaned)
   m=re.search(r' extends (.*?)(?: implements| \{)',cleaned)
   if m:parents.extend(x.strip().replace('.','/') for x in m[1].split(','))
   m=re.search(r' implements (.*?) \{',cleaned)
   if m:parents.extend(x.strip().replace('.','/') for x in m[1].split(','))
  m=re.search(r'descriptor: (\S+)',line)
  if not m or not i:continue
  desc=m[1];previous=lines[i-1].strip()
  if desc.startswith('('):
   n=re.search(r'([^\s(]+)\(',previous)
   if n:methods.add(('<init>' if n[1].replace('.','/')==owner else n[1],desc))
  else:
   n=re.search(r'([^\s;]+);$',previous)
   if n:fields.add((n[1],desc))
 definitions[owner]={'methods':methods,'fields':fields,'parents':parents}
 queue.extend(p for p in parents if p in boot and p not in definitions)
def resolves(owner,name,desc,kind,seen=None):
 seen=set() if seen is None else seen
 if owner in seen:return False
 seen.add(owner);item=definitions.get(owner,{})
 if (name,desc) in item.get(kind,set()):return True
 if name=='<init>':return False
 return any(resolves(p,name,desc,kind,seen) for p in item.get('parents',[]))
reports=[]
for name,(methods,fields) in refs.items():
 missingMethods=[{'owner':o,'method':n+d} for o,n,d in sorted(methods) if not resolves(o,n,d,'methods')]
 missingFields=[{'owner':o,'field':n+':'+d} for o,n,d in sorted(fields) if not resolves(o,n,d,'fields')]
 report={'module':name,'checked_methods':len(methods),'checked_fields':len(fields),'missing_methods':missingMethods,'missing_fields':missingFields,'hardware_verified':False,'scope':'Boot class direct descriptors + inheritance, not reflection/JNI/providers or behavior'}
 (stage/name/'api-audit.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
 print(name,'missing methods',len(missingMethods),'fields',len(missingFields),flush=True)
(ws/'kyf37-rom/all-stock-app-ports/api-audits.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Audited',len(reports),'apps and',len(definitions),'boot classes')
