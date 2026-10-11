from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port/backend-reference/Telecom')
for file,names in [('com/android/server/telecom/D.smali',['s','u','be']),('com/android/server/telecom/u.smali',['m']),('com/android/server/telecom/cl.smali',['u','v'])]:
 print(file)
 for b in re.findall(r'\.method.*?\.end method',(r/file).read_text(),re.S):
  if any(' '+n+'(' in b.splitlines()[0] for n in names):print(b[:8000])
