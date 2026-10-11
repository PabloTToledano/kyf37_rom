from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port/legacy-framework-smali')
for name,methods in {'android/telecom/Call':['absenceMemo','answerUnholding','destroy','getSubState','setCallFowarding'],'android/telecom/Call$SubState':['<clinit>'],'android/telecom/TelecomManager':['hasMultipleCallCapableAccounts','setReceiveMute','setIncallUiActiveState']}.items():
 p=r/(name+'.smali')
 if not p.exists():p=Path('/home/pablo/kyf37-rom/base-framework-smali')/(name+'.smali')
 if not p.exists():continue
 print('\nCLASS '+name)
 text=p.read_text()
 if name.endswith('SubState'):print('\n'.join(x for x in text.splitlines() if x.startswith('.field')))
 for block in re.findall(r'\.method.*?\.end method',text,re.S):
  if any(re.search(r'\s'+re.escape(n)+r'\(',block.splitlines()[0]) for n in methods):print(block)
