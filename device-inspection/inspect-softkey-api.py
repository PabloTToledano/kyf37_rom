from pathlib import Path
r=Path('/home/pablo/kyf37-rom/vendor-framework-smali/jp/kyocera/kcfp/util')
for name in ['KCfpSoftkeyGuide','KCfpSoftkeyGuide$Softkeys','KCfpSoftkeyGuide$Value']:
 print('\n'+name)
 print('\n'.join(l for l in (r/(name+'.smali')).read_text().splitlines() if l.startswith(('.method','.field'))))
