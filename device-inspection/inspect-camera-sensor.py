from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-rom/stock-system/vendor/lib')
for p in sorted(r.glob('*ov8856*')):
 print(p.name,p.stat().st_size)
 subprocess.run(['readelf','-d',str(p)],stdout=subprocess.PIPE)
for p in sorted(r.glob('*actuator*')):print(p.name)
print((Path('/home/pablo/kyf37-rom/irda-port-smali/com/kyocera/irda/client/IrDAClientSendActivity.smali')).read_text()[0:1500])
