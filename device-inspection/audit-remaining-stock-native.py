"""Audit candidate JNI dependency symbols; never claim ABI/namespace validation."""
from pathlib import Path
import subprocess,re,json,zipfile
here=Path(__file__).resolve().parent;ws=here.parent;tree=Path('/home/pablo/kyf37-android10');r=Path('/home/pablo/kyf37-rom');product=tree/'out/target/product/kyf37/system'
cache={}
def elf(p):
 if p in cache:return cache[p]
 text=subprocess.check_output(['readelf','-dW','--dyn-syms',str(p)],text=True)
 imports=set();exports=set()
 for line in text.splitlines():
  m=re.match(r'\s*\d+:\s+\S+\s+\S+\s+.+?\s+(GLOBAL|WEAK)\s+(DEFAULT|PROTECTED|HIDDEN)\s+(\S+)\s+(\S+)',line)
  if not m:continue
  binding,visibility,index,symbol=m.groups();symbol=symbol.split('@')[0]
  if index=='UND' and binding=='GLOBAL':imports.add(symbol)
  elif index!='UND' and visibility!='HIDDEN':exports.add(symbol)
 result={'needed':re.findall(r'\(NEEDED\).*?\[(.*?)\]',text),'imports':imports,'exports':exports};cache[p]=result;return result
providers={}
for base in [product/'lib',product/'vendor/lib',product/'apex/com.android.runtime/lib/bionic',product/'apex/com.android.runtime.debug/lib/bionic']:
 for p in base.glob('*.so'):
  if p.is_file() and p.read_bytes()[:4]==b'\x7fELF':providers[p.name]=p
for p in (tree/'out/soong/.intermediates').glob('**/android_arm_armv7-a-neon_cortex-a7_core_shared*/*.so'):
 if '.ndk' not in p.parent.parent.name and p.is_file():providers.setdefault(p.name,p)
reports=[]
for report in json.loads((ws/'kyf37-rom/all-stock-app-ports/assembly-reports.json').read_text()):
 work=r/'remaining-stock-ports'/report['stock_module']/'native-audit';work.mkdir(exist_ok=True)
 apk=tree/'packages/apps/Kyf37RemainingStockApps'/(report['build_module']+'.apk')
 with zipfile.ZipFile(apk) as z:
  local={}
  for name in z.namelist():
   if name.startswith('lib/armeabi-v7a/') and name.endswith('.so'):
    p=work/Path(name).name;p.write_bytes(z.read(name));local[p.name]=p
 for name,p in local.items():
  info=elf(p);symbols=set(info['exports']);queue=list(info['needed']);seen=set();missing=[];used={}
  while queue:
   dep=queue.pop()
   if dep in seen:continue
   seen.add(dep);provider=local.get(dep,providers.get(dep))
   if provider is None:missing.append(dep);continue
   data=elf(provider);symbols.update(data['exports']);queue.extend(data['needed']);used[dep]=str(provider)
  item={'module':report['stock_module'],'library':name,'missing_libraries':sorted(missing),'unresolved_strong_symbols':sorted(info['imports']-symbols),'providers':used}
  reports.append(item);print(item['module'],name,'missing libraries',len(missing),'missing symbols',len(item['unresolved_strong_symbols']),flush=True)
(ws/'kyf37-rom/all-stock-app-ports/native-audits.json').write_text(json.dumps({'files':reports,'scope':'Dependency strong symbol names only; linker namespaces, dlopen, symbol versions, JNI registration, struct/Binder/ioctl ABI and runtime behavior unverified.'},indent=2)+'\n')
