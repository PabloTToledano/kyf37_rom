"""Reconstruct monochrome poses from the owner's reference sheet (host Python/Pillow)."""
from pathlib import Path
import json
from PIL import Image
ws=Path(__file__).resolve().parent
im=Image.open(ws/'outer-animation/reference-sheet.png').convert('RGB')
columns=[(4,103,['General','Happy','Back turned','Sad','Eyes closed','Angry','Eating','No','Sitting','Running and falling','Surprised','Dizzy']),
 (249,349,['Badly behaved','Begging','Kissing','Fishing','Backpack','Bath','Brushing teeth','In bed','Close up']),
 (505,605,['Bow','Bow tie','Cap','Darts','Drum','Hair gel','Makeup','Music','Pen','Remote control','Roller skates']),
 (699,798,['Royal costume','Shirt','Shoes','Sunglasses','Throne','Trumpet','Umbrella','Weights','Wig','Wings'])]
sprites=[];scenes=[]
for x0,x1,labels in columns:
 for row,label in enumerate(labels):
  y0=5+row*48;y1=y0+39
  if label=='Close up':y0=425;y1=467
  if label=='Pen':y0=387;y1=417
  if label=='Remote control':y0=455;y1=495
  if label=='Roller skates':y0=503;y1=543
  crop=im.crop((x0,y0,x1,y1))
  black=lambda x,y:max(crop.getpixel((x,y)))<120
  occupied=[x for x in range(crop.width) if any(black(x,y) for y in range(crop.height))]
  groups=[]
  for x in occupied:
   if not groups or x-groups[-1][-1]>=10:groups.append([])
   groups[-1].append(x)
  start=len(sprites)
  for g in groups:
   ys=[y for y in range(crop.height) if any(black(x,y) for x in g)]
   w=g[-1]-g[0]+1;h=max(ys)-min(ys)+1
   pixels=[int(black(x,y)) for y in range(min(ys),max(ys)+1) for x in range(g[0],g[-1]+1)]
   assert w<=40 and h<=36,(label,w,h)
   sprites.append({'w':w,'h':h,'pixels':pixels,'label':label})
  assert len(sprites)>start,label
  scenes.append({'label':label,'start':start,'count':len(sprites)-start})
lines=['/* Owner-supplied reference sheet; black source pixels become lit OLED pixels. */',
 'struct PetPose {int w,h;const unsigned char *p;};']
for i,s in enumerate(sprites):lines.append('static const unsigned char pose_%d[]={%s};'%(i,','.join(map(str,s['pixels']))))
lines.append('static const struct PetPose pet_poses[]={'+','.join('{%d,%d,pose_%d}'%(s['w'],s['h'],i) for i,s in enumerate(sprites))+'};')
lines.append('static const int scene_start[]={'+','.join(str(s['start']) for s in scenes)+'};')
lines.append('static const int scene_count[]={'+','.join(str(s['count']) for s in scenes)+'};')
lines.append('#define PET_SCENES %d'%len(scenes))
(ws/'outer-animation/reference-poses.h').write_text('\n'.join(lines)+'\n')
(ws/'outer-animation/reference-scenes.json').write_text(json.dumps(scenes,indent=2))
print('Extracted',len(sprites),'poses across',len(scenes),'coherent scenes')

