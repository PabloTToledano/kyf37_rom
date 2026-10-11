import zipfile, subprocess
from pathlib import Path

for p in sorted(Path('/home/pablo/microg').glob('*.apk')):
    print('===', p.name, '===')
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            if name.startswith('META-INF/') and (name.endswith('.RSA') or name.endswith('.DSA') or name.endswith('.EC')):
                data = z.read(name)
                res = subprocess.run(['openssl', 'pkcs7', '-inform', 'DER', '-print_certs', '-noout', '-text'], input=data, capture_output=True)
                for line in res.stdout.decode('utf-8', errors='ignore').splitlines():
                    if 'Subject:' in line or 'Issuer:' in line or 'Fingerprint' in line:
                        print(' ', line)
