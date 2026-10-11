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
# Audit installed payloads, not historical proprietary or linker intermediates.
# Source-built display aliases now replace the old default-namespace providers.
for base in [product/'system/vendor/lib',product/'system/lib',product/'system/apex/com.android.runtime/lib/bionic',product/'system/vendor/lib/egl',product/'system/lib/egl']:
 for p in base.glob('*.so'):
  if elf(p): providers[p.name]=p
for rel in ['lib/liboverlay.so','lib/libhdmi.so','lib/libqdutils.so','lib/libmemalloc.so','lib/libqdMetaData.so','lib/libqservice.so','vendor/lib/hw/hwcomposer.msm8909.so','vendor/lib/hw/gralloc.msm8909.so']:
 if rel not in candidate:candidate.append(rel)
reports=[]
# These two camera-only libraries resolve legacy symbols from the explicit
# provider preload. Check the installed init definition and shim, not source intent.
camera_rc=product/'system/etc/init/init.kyf37.camera.rc'
camera_preload=product/'system/vendor/lib/libkyf37_jpegcompat.so'
preload_exports=set()
if camera_rc.is_file():
 rc=camera_rc.read_text()
 service=re.search(r'^service vendor\.camera-provider-2-4 .*?(?=^service |\Z)',rc,re.M|re.S)
 if service and '    setenv LD_PRELOAD /vendor/lib/libkyf37_jpegcompat.so' in service[0]:
  preload=elf(camera_preload)
  if preload:preload_exports=preload['exports']
for rel in candidate:
 p=product/'system'/rel;info=elf(p)
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
 direct_missing=info['imports']-symbols
 preloaded=direct_missing & preload_exports if rel in ('vendor/lib/libfastcvopt.so','vendor/lib/libmmqjpeg_codec.so') else set()
 reports.append({'file':rel,'missing_libraries':sorted(missing_libraries),
  'unresolved_strong_symbols':sorted(direct_missing-preloaded),'providers':deps,
  'direct_dependency_unresolved_symbols':sorted(direct_missing),
  'camera_provider_preload_symbols':sorted(preloaded),
  'preload_scope':'Only camera provider; other callers require their own compatibility audit' if preloaded else None})
(args.report or host/'vendor-symbol-audit.json').write_text(json.dumps({'target':args.label,
 'files':reports,'note':'ELF dependency closure and strong symbol-name audit. Missing providers may not be built yet. Ignores ELF symbol versions, loader caller/global namespace, dlopen, structure/layout/ioctl ABI. Findings need runtime/ABI review; no compatibility claim.'},indent=2))
print('Checked',len(reports),'vendor ELF files')
for x in reports:
 if x['missing_libraries'] or x['unresolved_strong_symbols']:
  print(x['file'],'missing libraries:',len(x['missing_libraries']),'unresolved symbols:',len(x['unresolved_strong_symbols']))
