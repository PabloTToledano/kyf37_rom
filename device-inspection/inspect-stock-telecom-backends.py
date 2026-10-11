from pathlib import Path
import subprocess,re
r=Path('/home/pablo/kyf37-rom');stage=r/'stock-dialer-port/backend-reference';stage.mkdir(exist_ok=True)
java='/home/pablo/kyf37-host-tools/jdk8/bin/java'
for name in ['Telecom','TeleService']:
 dex=r/f'deoptimized-apps/priv-app/{name}/{name}.dex'
 out=stage/name
 if not out.exists():subprocess.run([java,'-jar',str(r/'tools/baksmali.jar'),'disassemble',str(dex),'-o',str(out)],check=True)
 methods=['setReceiveMute','setHeardEffect','setCallFowarding','startTalkingMemo','absenceMemo','setIncallUiActiveState']
 matches=[]
 for p in out.rglob('*.smali'):
  text=p.read_text()
  for b in re.findall(r'\.method.*?\.end method',text,re.S):
   if any(' '+n+'(' in b.splitlines()[0] for n in methods):matches.append(str(p.relative_to(out))+'\n'+b)
 (stage/(name+'-methods.txt')).write_text('\n\n'.join(matches))
 print(name,'matching methods:',len(matches))
