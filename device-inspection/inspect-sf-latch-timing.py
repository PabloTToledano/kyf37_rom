from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
p=r/'frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp'
for i,l in enumerate(p.read_text().splitlines()):
 if 'latch_unsignaled' in l or 'backpressure' in l:print(i+1,l)
p=r/'device/kyocera/kyf37/device.mk'
for l in p.read_text().splitlines():
 if 'vsync' in l or 'sf.' in l:print(l)
