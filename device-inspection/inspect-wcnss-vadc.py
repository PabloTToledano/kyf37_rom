from pathlib import Path
r=Path('/home/pablo/kyf37-rom/kernel-android10')
for p in r.glob('drivers/**/wcnss*.c'):
 s=p.read_text();a=s.find('vadc get failed')
 if a>=0:print(p,s[a-900:a+600])
p=Path('/home/pablo/kyf37-rom/kernel-android10-gcc48-build/.config')
for l in p.read_text().splitlines():
 if any(x in l for x in ['QPNP_ADC','QPNP_VADC','QPNP_SPMI','SPMI']):print(l)
