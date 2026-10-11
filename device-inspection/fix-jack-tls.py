from pathlib import Path
import zipfile, struct

# Jack 1.3 selects SSLv3 SSLContext, whose defaults cannot negotiate with a
# current JDK/curl. Select TLSv1.2 without relaxing certificate verification.
paths = [Path('/home/pablo/kyf37-lineage/prebuilts/sdk/tools/jack-server-4.8.ALPHA.jar'),
         Path('/home/pablo/.jack-server/server-1.jar')]
name = 'com/android/jack/server/JackHttpServer.class'
old = b'\x01\x00\x05SSLv3'
new = b'\x01\x00\x07TLSv1.2'
for p in paths:
    with zipfile.ZipFile(p) as z:
        files = [(i, z.read(i.filename)) for i in z.infolist()]
    data = dict((i.filename, b) for i,b in files)[name]
    if old not in data:
        assert new in data
        continue
    assert data.count(old) == 1
    backup = p.with_suffix('.jar.before-tls-fix')
    if not backup.exists(): backup.write_bytes(p.read_bytes())
    tmp = p.with_suffix('.jar.tmp')
    with zipfile.ZipFile(tmp, 'w') as z:
        for info, b in files:
            z.writestr(info, b.replace(old,new,1) if info.filename == name else b)
    tmp.replace(p)
    print('Selected TLSv1.2 in', p)
