from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port/backend-reference/Telecom')
for p in r.rglob('*.smali'):
 for b in re.findall(r'\.method.*?\.end method',p.read_text(),re.S):
  if any(' '+n+'(' in b.splitlines()[0] for n in ['setIncallUiActiveState','answerUnholding','setCallFowarding']):
   print(str(p.relative_to(r))+'\n'+b[:5500])
