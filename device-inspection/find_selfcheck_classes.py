import zipfile, subprocess, re

with zipfile.ZipFile('/home/pablo/microg/com.google.android.gms-252432034.apk') as z:
    for n in z.namelist():
        if n.endswith('.dex'):
            data = z.read(n)
            matches = re.findall(rb'Lorg/microg/gms/ui/[a-zA-Z0-9_/$]*;', data)
            for m in set(matches):
                s = m.decode()
                if 'Check' in s:
                    print(s)
