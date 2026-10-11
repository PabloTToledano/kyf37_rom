from pathlib import Path
r=Path('/home/pablo/kyf37-rom/stock-system')
for p in r.rglob('*.so'):
 if any(x in p.name for x in ['stats','tintless','actuator_rohm']):print(p.relative_to(r))
