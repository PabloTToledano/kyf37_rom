import struct,json,zipfile,sys,os
from pathlib import Path
from loguru import logger
from androguard.core.dex import DEX
logger.remove()
def parse(b):
 o=8
 def u(n):
  nonlocal o
  v=int.from_bytes(b[o:o+n],'big');o+=n;return v
 cp=[None]*u(2);i=1
 while i<len(cp):
  tag=u(1)
  if tag==1:n=u(2);cp[i]=b[o:o+n].decode('utf8','replace');o+=n
  elif tag==7:cp[i]=('class',u(2))
  elif tag in [8,16,19,20]:u(2)
  elif tag in [3,4,9,10,11,12,17,18]:u(4)
  elif tag in [5,6]:u(8);i+=1
  elif tag==15:u(3)
  else:raise ValueError(tag)
  i+=1
 u(2);this=u(2);sup=u(2);interfaces=[u(2) for _ in range(u(2))]
 def classname(n):return cp[cp[n][1]] if n else None
 def attributes():
  nonlocal o
  for _ in range(u(2)):u(2);n=u(4);o+=n
 for _ in range(u(2)):u(2);u(2);u(2);attributes()
 methods=set()
 for _ in range(u(2)):
  u(2);name=u(2);desc=u(2);methods.add((cp[name],cp[desc]));attributes()
 return {'super':classname(sup),'interfaces':[classname(n) for n in interfaces],'methods':methods}
framework_jar=os.environ.get('KYF37_AUDIT_FRAMEWORK_JAR','kyf37-rom/android-7-framework-classes.jar')
sdk_jar=os.environ.get('KYF37_AUDIT_SDK_JAR','kyf37-rom/android-7-sdk-classes.jar')
with zipfile.ZipFile(framework_jar) as z:
 classes={n[:-6]:parse(z.read(n)) for n in z.namelist() if n.endswith('.class')}
with zipfile.ZipFile(sdk_jar) as z:
 for n in z.namelist():
  if n.endswith('.class') and n[:-6] not in classes:classes[n[:-6]]=parse(z.read(n))
def contains(c,n,desc,seen=None):
 seen=set() if seen is None else seen
 if c in seen or c not in classes:return False
 seen.add(c);cl=classes[c]
 return (n,desc) in cl['methods'] or (n!='<init>' and any(contains(p,n,desc,seen) for p in [cl['super']]+cl['interfaces'] if p))
d=DEX(Path(sys.argv[1] if len(sys.argv)>1 else 'kyf37-rom/AfpHome-reconstructed.dex').read_bytes());owned={c.get_name()[1:-1]:c for c in d.get_classes()};missing=[];vendor=[];checked=0;internal_missing=[]
def owned_contains(c,n,desc,seen=None):
 seen=set() if seen is None else seen
 if c in seen:return False
 seen.add(c)
 if c not in owned:return contains(c,n,desc)
 cl=owned[c]
 if any(m.get_name()==n and m.get_descriptor().replace(' ','')==desc for m in cl.get_methods()):return True
 if n=='<init>':return False
 parents=[cl.get_superclassname()[1:-1]]+[p[1:-1] for p in cl.get_interfaces()]
 return any(owned_contains(p,n,desc,seen) for p in parents)
for m in d.get_methods():
 c=m.get_class_name()[1:-1];n=m.get_name();desc=m.get_descriptor().replace(' ','')
 ref={'class':c,'method':n,'descriptor':desc}
 if c in owned:
  if not owned_contains(c,n,desc):internal_missing.append(ref)
  continue
 if c.startswith(('android/','com/android/internal/')):
  checked+=1
  if not contains(c,n,desc):missing.append(ref)
 elif c.startswith(('jp/kyocera/','com/nextfp/')):vendor.append(ref)
report={'target':os.environ.get('KYF37_AUDIT_TARGET','Android7.1.2 compiled framework'),'framework_jar':framework_jar,'sdk_jar':sdk_jar,'framework_methods_checked':checked,'missing_framework_methods':missing,'vendor_framework_method_dependencies':vendor,'unresolved_owned_class_method_references':internal_missing,'note':'Static method reference audit, not runtime verification. For public-SDK-only inputs, unresolved methods may be hidden platform APIs rather than removed APIs. Fields, dynamic/reflection dependencies and resources are outside this check.'}
Path(sys.argv[2] if len(sys.argv)>2 else 'kyf37-rom/afphome-api-compatibility.json').write_text(json.dumps(report,indent=2))
print('Checked',checked,'missing',len(missing),'vendor dependencies',len(vendor),'unresolved owned methods',len(internal_missing))
for x in missing[:15]:print(x)
