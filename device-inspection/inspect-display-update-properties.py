from pathlib import Path
r=Path('/home/pablo/kyf37-android10/hardware/qcom-caf/msm8916/display')
for p in r.rglob('*'):
 if p.suffix not in ['.cpp','.h']:continue
 for i,l in enumerate(p.read_text(errors='replace').splitlines()):
  if ('property_get' in l or 'property_set' in l) and any(t in l.lower() for t in ['partial','swap','gpu','comp','debug']):print(str(p.relative_to(r))+':'+str(i+1)+':'+l.strip())
print('TEST FILES')
for p in Path('/home/pablo/kyf37-android10/frameworks/base/packages/SettingsLib').rglob('*WifiMacAddress*'):print(p)

