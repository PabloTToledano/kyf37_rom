from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port')
for file,names in [('backend-reference/Telecom/com/android/server/telecom/u.smali',['m']),('backend-reference/Telecom/com/android/server/telecom/D.smali',['be']),('smali/com/android/incallui/TelecomAdapter.smali',['setCallFowarding']),('smali/com/android/incallui/Call.smali',['setCallFowarding'])]:
 for b in re.findall(r'\.method.*?\.end method',(r/file).read_text(),re.S):
  if any(' '+n+'(' in b.splitlines()[0] for n in names):print(file+'\n'+b)
