"""Reframe Bad Apple for the 128x36 outer panel; preserve timing and all vertical content."""
from pathlib import Path
import subprocess,gzip,json,hashlib,os
import numpy as np
from PIL import Image
w=Path(__file__).resolve().parent.parent
p=w/'third-party/bad-apple';a=p/'assets';source=p/'BadApple.mp4'
def linux(path):
 s=str(path.resolve()).replace('\\','/');return '/mnt/'+s[0].lower()+s[2:] if os.name=='nt' else s
cmd=['ffmpeg','-v','error','-i',linux(source),'-vf','fps=15,scale=128:96:flags=area,format=gray','-f','rawvideo','-pix_fmt','gray','-']
if os.name=='nt':cmd=['wsl','-d','Ubuntu','--']+cmd
raw=subprocess.check_output(cmd)
frames=np.frombuffer(raw,np.uint8).reshape(-1,96,128)
candidates=[];backgrounds=[];cuts=[]
for i,f in enumerate(frames):
 corners=np.concatenate((f[:8,:8].ravel(),f[:8,-8:].ravel(),f[-8:,:8].ravel(),f[-8:,-8:].ravel()))
 bg=255 if np.median(corners)>=128 else 0;backgrounds.append(bg)
 fg=(f<128) if bg else (f>=128)
 y,x=np.nonzero(fg)
 width=80
 if len(x)>80:
  span=int(x.max()-x.min()+1);height=int(y.max()-y.min()+1)
  spread=(np.count_nonzero(x<32)/len(x)>.12 and np.count_nonzero(x>=96)/len(x)>.12)
  if span>=108 and (height<=72 or spread):width=128
  elif span>=100:width=104
 candidates.append(width)
 if i and np.mean(np.abs(f.astype(np.int16)-frames[i-1]))>95:cuts.append(i)
# A rolling vote prevents isolated pixels/fast gestures changing the framing.
targets=[int(np.median(candidates[max(0,i-12):min(len(frames),i+13)])) for i in range(len(frames))]
packed=bytearray();widths=[];width=targets[0];cutset=set(cuts)
preview=[]
for i,f in enumerate(frames):
 target=targets[i]
 if i in cutset:width=target
 else:width+=max(-2,min(2,target-width))
 widths.append(width)
 # Extend the shot's background to the panel edges, rather than pillarbox white shots.
 canvas=Image.new('L',(128,36),backgrounds[i])
 canvas.paste(Image.fromarray(f).resize((width,36),Image.Resampling.BOX),((128-width)//2,0))
 binary=np.asarray(canvas)>=128
 packed.extend(np.packbits(binary,axis=None,bitorder='big').tobytes())
 if i in (90,450,900,1350,1800,2250,2700,3150):preview.append((i,Image.fromarray((binary*255).astype(np.uint8)),width))
with gzip.GzipFile(filename=str(a/'badapple.frames.gz'),mode='wb',mtime=0) as out:out.write(packed)
info=json.loads((p/'provenance.json').read_text()) if (p/'provenance.json').exists() else {'source':'https://raw.githubusercontent.com/rkk-2s/bad-apple/master/BadApple.mp4','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fps':15}
info.update(display='Adaptive 80–128x36, extended shot background, full vertical frame',framing={'minimum_width':min(widths),'maximum_width':max(widths),'full_width_frames':widths.count(128),'widths':{str(k):widths.count(k) for k in sorted(set(widths))}},frames=len(frames),size=len(packed))
(p/'provenance.json').write_text(json.dumps(info,indent=2))
# Local visual QA, including a representative full-width shot.
full=next((i for i in range(150,len(frames)) if widths[i]==128 and np.std(frames[i])>50),None)
if full is not None:
 bits=np.unpackbits(np.frombuffer(packed[full*576:(full+1)*576],np.uint8)).reshape(36,128)*255
 preview.append((full,Image.fromarray(bits),128))
outdir=w/'device-inspection/outer-animation';sheet=Image.new('RGB',(768,180*len(preview)),'#202830')
from PIL import ImageDraw
draw=ImageDraw.Draw(sheet)
for j,(i,im,width) in enumerate(preview):
 draw.text((8,j*180+4),f'{i/15:.1f}s  image width {width}px / panel 128px',fill='white')
 sheet.paste(im.resize((768,144),Image.Resampling.NEAREST),(0,j*180+28))
sheet.save(outdir/'badapple-wide-preview.png')
assert len(packed)==3286*576 and min(widths)>=80 and max(widths)==128 and widths.count(128)>30
print(json.dumps({'frames':len(frames),'width_range':[min(widths),max(widths)],'full_width_frames':widths.count(128),'gzip_bytes':(a/'badapple.frames.gz').stat().st_size}))
