from pathlib import Path
r=Path('/home/pablo/kyf37-rom')
for p in (r/'irda-port-smali').rglob('*.smali'):
 if 'isUartUseStart' in p.read_text():print(p)
for p in (r/'stock-system').rglob('*.so'):
 if any(x in p.name for x in ['sensor','chromatix','mmcamera_faceproc']):print(p)
