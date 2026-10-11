"""Offline class-reference audit of the stock phone test port; no stubbed call control."""
from pathlib import Path
import re,json,zipfile
r=Path('/home/pablo/kyf37-rom');root=Path('/home/pablo/kyf37-android10');stage=r/'stock-dialer-port'
known=set();refs=set()
for p in (stage/'smali').rglob('*.smali'):
 text=p.read_text();m=re.search(r'^\.class[^\n]*? L([^;]+);',text,re.M)
 if m:known.add(m[1])
 refs.update(x for x in re.findall(r'L((?:android|com/android|jp/kyocera)/[^;\s]+);',text) if '<' not in x)
for p in (r/'kyocera-compat-stage').rglob('*.smali'):
 m=re.search(r'^\.class[^\n]*? L([^;]+);',p.read_text(),re.M)
 if m:known.add(m[1])
for module in ['framework','telephony-common','voip-common','ims-common','core-oj','core-libart','ext']:
 p=root/f'out/target/common/obj/JAVA_LIBRARIES/{module}_intermediates/classes.jar'
 if p.exists():
  with zipfile.ZipFile(p) as z:known.update(n[:-6] for n in z.namelist() if n.endswith('.class'))
metadata=sorted(x for x in refs-known if '.' in x)
missing=sorted(x for x in refs-known if '.' not in x)
report={'referenced_framework_vendor_classes':len(refs),'missing_classes':missing,'metadata_only_descriptors':metadata,'scope':'Class existence only, not method/field signatures, dynamic reflection or call behavior.'}
(stage/'class-audit.json').write_text(json.dumps(report,indent=2))
print('Class references:',len(refs),'Missing:',len(missing));print('\n'.join(missing))
folder=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/stock-dialer-port')
(folder/'class-audit.json').write_text(json.dumps(report,indent=2))
