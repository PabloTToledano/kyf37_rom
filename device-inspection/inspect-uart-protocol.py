from pathlib import Path
s=Path('/home/pablo/kyf37-rom/felica-port-smali/jp/kyocera/felicaservice/a.smali').read_text()
for signature in ['.method public final E()I','.method public final F()Z']:
 a=s.find(signature);b=s.find('.end method',a);print(s[a:b+11])
