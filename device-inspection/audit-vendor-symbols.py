from pathlib import Path
import subprocess,re,json,hashlib,argparse

parser=argparse.ArgumentParser(description='Audit selected vendor ELF symbol dependency closure against a chosen product tree.')
parser.add_argument('--tree',type=Path,default=Path('/home/pablo/kyf37-lineage'))
parser.add_argument('--report',type=Path)
parser.add_argument('--label',default='Current incomplete Android7.1 build')
args=parser.parse_args()

host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
stock=Path('/home/pablo/kyf37-rom/stock-system')
tree=args.tree
product=tree/'out/target/product/kyf37'
candidate=[x for x in (tree/'vendor/kyocera/kyf37/proprietary-files.txt').read_text().splitlines() if x]
cache={}
def elf(p):
 if p in cache:return cache[p]
 if not p.is_file() or p.read_bytes()[:4]!=b'\x7fELF':return None
 data=subprocess.check_output(['readelf','-dW','--dyn-syms',str(p)],text=True)
 needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',data)
 exports=set();imports=set()
 for line in data.splitlines():
  # readelf may spell ARM GNU_IFUNC as the multiword "<OS specific>: 10".
  m=re.match(r'\s*\d+:\s+\S+\s+\S+\s+.+?\s+(GLOBAL|WEAK)\s+(DEFAULT|PROTECTED|HIDDEN)\s+(\S+)\s+(\S+)',line)
  if not m:continue
  binding,visibility,index,symbol=m.groups();symbol=symbol.split('@')[0]
  if index=='UND':
   if binding=='GLOBAL':imports.add(symbol)
  elif visibility!='HIDDEN':exports.add(symbol)
 r={'needed':needed,'exports':exports,'imports':imports};cache[p]=r;return r
providers={}
# Soong packages core libraries (notably bionic in the runtime APEX) outside
# the old Make intermediates. Use linked core variants as incomplete-build
# fallbacks; actual installed files and explicit proprietary choices win below.
for p in (tree/'out/soong/.intermediates').glob('**/android_arm_armv7-a-neon_cortex-a7_core_shared*/*.so'):
 if not re.fullmatch(r'android_arm_armv7-a-neon_cortex-a7_core_shared(?:_com\..+)?',p.parent.name):continue
 if '.ndk' in p.parent.parent.name:continue
 if elf(p):providers.setdefault(p.name,p)
for base in [product/'system/lib',product/'system/vendor/lib',product/'system/apex/com.android.runtime/lib/bionic',product/'system/apex/com.android.runtime.debug/lib/bionic']:
 for p in base.glob('*.so'):
  if elf(p):providers[p.name]=p
# Prefer linked platform providers over stale output, then apply the product's
# explicit proprietary selections (copy recipes override source installations).
for module in (product/'obj/SHARED_LIBRARIES').glob('*_intermediates'):
 name=module.name.removesuffix('_intermediates')+'.so'
 # These Make intermediates are SDK link stubs on Android 10. The runtime
 # APEX/core ELF above contains the real private and deprecated ARM exports.
 if name in ('libc.so','libm.so','libdl.so'):continue
 for p in [module/'LINKED'/name,module/name]:
  if elf(p):providers[name]=p;break
for rel in candidate:
 if rel.startswith(('lib/','vendor/lib/')) and rel.endswith('.so') and '/hw/' not in rel:
  p=tree/'vendor/kyocera/kyf37/proprietary'/rel
  if elf(p):providers[p.name]=p
reports=[]
for rel in candidate:
 p=tree/'vendor/kyocera/kyf37/proprietary'/rel;info=elf(p)
 if not info:continue
 symbols=set(info['exports']);missing_libraries=set();visited=set();queue=list(info['needed']);deps=[]
 while queue:
  name=queue.pop()
  if name in visited:continue
  visited.add(name)
  provider=providers.get(name)
  if not provider:
   missing_libraries.add(name);continue
  dep=elf(provider)
  symbols.update(dep['exports']);queue.extend(dep['needed'])
  original=stock/'lib'/name
  same=original.is_file() and hashlib.sha256(provider.read_bytes()).digest()==hashlib.sha256(original.read_bytes()).digest()
  deps.append({'library':name,'provider':str(provider),'same_as_stock':same})
 reports.append({'file':rel,'missing_libraries':sorted(missing_libraries),
  'unresolved_strong_symbols':sorted(info['imports']-symbols),'providers':deps})
(args.report or host/'vendor-symbol-audit.json').write_text(json.dumps({'target':args.label,
 'files':reports,'note':'ELF dependency closure and strong symbol-name audit. Missing providers may not be built yet. Ignores ELF symbol versions, loader caller/global namespace, dlopen, structure/layout/ioctl ABI. Findings need runtime/ABI review; no compatibility claim.'},indent=2))
print('Checked',len(reports),'vendor ELF files')
for x in reports:
 if x['missing_libraries'] or x['unresolved_strong_symbols']:
  print(x['file'],'missing libraries:',len(x['missing_libraries']),'unresolved symbols:',len(x['unresolved_strong_symbols']))
