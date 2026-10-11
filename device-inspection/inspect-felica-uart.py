from pathlib import Path
r=Path('/home/pablo/kyf37-rom/felica-port-smali')
for p in r.rglob('*.smali'):
 s=p.read_text()
 if 'isUartUseStart' in s or 'uartUseFinish' in s:
  print(p)
  if '.method public isUartUseStart' in s:print(s)
