from pathlib import Path
import struct, shutil, json,argparse
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('--input',default='kyf37-rom/stock-selector-assets/res')
parser.add_argument('--output',default='kyf37-rom/selector-source/res')
args=parser.parse_args()
root=Path(args.input)
out=Path(args.output)
def chunk(data):
    offset=8
    while offset<len(data):
        length=struct.unpack_from('>I',data,offset)[0]
        tag=data[offset+4:offset+8]
        body=data[offset+8:offset+8+length]
        offset+=length+12
        if tag==b'npTc': return body
    raise ValueError('Missing compiled nine-patch chunk')
report=[]
for p in root.rglob('*'):
    if not p.is_file(): continue
    dest=out/p.relative_to(root)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not p.name.endswith('.9.png'):
        shutil.copy2(p,dest)
        continue
    data=chunk(p.read_bytes())
    nx,ny=data[1:3]
    assert nx%2==ny%2==0
    left,right,top,bottom=struct.unpack_from('>4i',data,12)
    divs=struct.unpack_from('>'+str(nx+ny)+'i',data,32)
    original=Image.open(p).convert('RGBA')
    w,h=original.size
    img=Image.new('RGBA',(w+2,h+2),(0,0,0,0))
    img.paste(original,(1,1))
    def line(axis,start,end):
        assert 0<=start<end<=(w if axis in ('top','bottom') else h)
        for v in range(start,end):
            pos={'top':(v+1,0),'bottom':(v+1,h+1),
                 'left':(0,v+1),'right':(w+1,v+1)}[axis]
            img.putpixel(pos,(0,0,0,255))
    for a,b in zip(divs[:nx:2],divs[1:nx:2]): line('top',a,b)
    for a,b in zip(divs[nx::2],divs[nx+1::2]): line('left',a,b)
    line('bottom',left,w-right)
    line('right',top,h-bottom)
    assert img.crop((1,1,w+1,h+1)).tobytes()==original.tobytes()
    img.save(dest)
    report.append({'file':str(dest),'x_divs':divs[:nx],'y_divs':divs[nx:],
                   'padding':[left,right,top,bottom],'pixels_preserved':True})
(out.parent/'conversion.json').write_text(json.dumps(report,indent=2))
print('Decoded',len(report),'nine-patches with original pixels and stretch/padding metadata')
