import ctypes,subprocess,tempfile,json
from pathlib import Path
app=Path.home()/'kyf37-android10/packages/apps/Kyf37OuterScreen'
out=Path(__file__).resolve().parent/'outer-animation'
with tempfile.TemporaryDirectory() as tmp:
 so=Path(tmp)/'render.so'
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-shared','-fPIC',str(app/'render.c'),'-o',str(so)],check=True)
 lib=ctypes.CDLL(str(so));fn=lib.kyf37_subdisplay_animation
 fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t]+[ctypes.c_int]*5
 idle=lib.kyf37_subdisplay_idle;idle.argtypes=[ctypes.c_void_p,ctypes.c_size_t]+[ctypes.c_int]*4
 clock=(ctypes.c_ubyte*4608)();assert idle(clock,4608,9,41,80,0)==0
 idleframes=[]
 for phase in range(4):
  assert idle(clock,4608,9,41,80,phase)==0;idleframes.append(bytes(clock))
 assert len(set(idleframes))>=3
 previews=[]
 for scene in range(42):
  frames=[]
  for frame in range(48):
   buf=(ctypes.c_ubyte*4610)();buf[0]=173;buf[-1]=219
   assert fn(ctypes.byref(buf,1),4608,frame,9,41,80,scene)==0
   assert buf[0]==173 and buf[-1]==219
   pixels=bytes(buf)[1:-1];assert set(pixels)<={0,1}
   frames.append(pixels)
  assert frames[0]==frames[-1]==idleframes[0]
  assert len(set(frames))>=20
  if scene in (6,15,25,32,41):previews.extend(frames)
 for frame,scene in [(-1,0),(48,0),(0,-1),(0,42)]:
  assert fn(ctypes.byref(buf,1),4608,frame,9,41,80,scene)==-1
 assert fn(None,4608,0,9,41,80,0)==-1
 (out/'frames.bin').write_bytes(b''.join(previews))
print('PASS: 42 scenes / 2016 frames, clock endpoints, animated idle, guards and invalid arguments')
