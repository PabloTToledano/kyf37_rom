from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port/backend-reference/Telecom')
for p in r.rglob('*.smali'):
 text=p.read_text()
 for b in re.findall(r'\.method.*?\.end method',text,re.S):
  if any(k in b.splitlines()[0].lower() for k in ['selectsaveautotalk','heardeffect','switchtootheractivesub']):print(str(p.relative_to(r))+'\n'+b[:4500])
# Modern camera capability members, not shell expansion of nested class names.
p=Path('/home/pablo/kyf37-android10/frameworks/base/telecomm/java/android/telecom/VideoProfile.java')
print('\n'.join(l for l in p.read_text().splitlines() if any(x in l for x in ['getMaxZoom','isZoomSupported','getWidth','getHeight'])))
