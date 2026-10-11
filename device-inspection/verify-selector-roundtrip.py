import io, json, struct, zipfile
from pathlib import Path
from PIL import Image

def metadata(data):
    pos=8
    while pos<len(data):
        size=struct.unpack_from('>I',data,pos)[0]
        kind=data[pos+4:pos+8];body=data[pos+8:pos+8+size]
        pos+=size+12
        if kind==b'npTc':
            nx,ny=body[1:3]
            return {'x_y_divs':struct.unpack_from('>'+str(nx+ny)+'i',body,32),
                    'padding':struct.unpack_from('>4i',body,12)}
    raise ValueError('Missing nine-patch')
root=Path('kyf37-rom');report=[]
with zipfile.ZipFile(root/'selector-compile-check.apk') as z:
    for src in (root/'stock-selector-assets/res').rglob('*.9.png'):
        key='res/'+src.relative_to(root/'stock-selector-assets/res').as_posix()
        before=src.read_bytes();after=z.read(key)
        same_metadata=metadata(before)==metadata(after)
        a=Image.open(io.BytesIO(before)).convert('RGBA')
        b=Image.open(io.BytesIO(after)).convert('RGBA')
        same_pixels=a.size==b.size and a.tobytes()==b.tobytes()
        report.append({'file':key,'same_stretch_and_padding':same_metadata,
                       'same_pixels':same_pixels})
        assert same_metadata and same_pixels,report[-1]
(root/'selector-roundtrip-verification.json').write_text(json.dumps(report,indent=2))
print('Original pixels, stretch regions and padding preserved for',len(report),'compiled nine-patches')
