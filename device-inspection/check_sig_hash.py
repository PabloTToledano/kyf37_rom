import zipfile, subprocess
from pathlib import Path

for p in sorted(Path('/home/pablo/microg').glob('*.apk')):
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            if name.startswith('META-INF/') and (name.endswith('.RSA') or name.endswith('.DSA') or name.endswith('.EC')):
                data = z.read(name)
                # extract DER certs with openssl
                res = subprocess.run(['openssl', 'pkcs7', '-inform', 'DER', '-print_certs', '-outform', 'DER'], input=data, capture_output=True)
                der = res.stdout
                h = 1
                for b in der:
                    h = (31 * h + (b if b < 128 else b - 256)) & 0xffffffff
                # Also to hex
                print(f'{p.name}: der_len={len(der)} hash={h:08x}')
