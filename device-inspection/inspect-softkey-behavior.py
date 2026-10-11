from pathlib import Path
import re
p=Path('/home/pablo/kyf37-rom/vendor-framework-smali/jp/kyocera/kcfp/util/KCfpSoftkeyGuide.smali')
for b in re.findall(r'\.method.*?\.end method',p.read_text(),re.S):
 if any(' '+n+'(' in b.splitlines()[0] for n in ['hide','show','translucent','pendingApply','setResource']):print(b[:5200])
