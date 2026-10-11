"""Offline JVM checks for billing cycles: equality, leap years and Spanish DST."""
from pathlib import Path
import subprocess,json
here=Path(__file__).resolve().parent
out=Path('/home/pablo/kyf37-rom/stock-cycle-tests');out.mkdir(exist_ok=True)
java=Path('/home/pablo/kyf37-host-tools/jdk8/bin')
subprocess.run([str(java/'javac'),'-d',str(out),str(here/'kyocera-port/Kyf37MonthlyCycle.java'),str(here/'kyocera-port/Kyf37MonthlyCycleTest.java')],check=True)
result=subprocess.check_output([str(java/'java'),'-cp',str(out),'Kyf37MonthlyCycleTest'],text=True)
(here.parent/'kyf37-rom/all-stock-app-ports/cycle-tests.json').write_text(json.dumps({'passed':True,'output':result.strip(),'hardware_accessed':False,'scope':'Monthly boundary calculation only; Android service/reflection/provider execution unverified'},indent=2)+'\n')
print(result,end='')
