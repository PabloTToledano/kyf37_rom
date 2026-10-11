import zipfile, subprocess

p = '/mnt/c/Users/pablo/Downloads/phone_GmsCore.apk'
with zipfile.ZipFile(p) as z:
    for n in z.namelist():
        if n.startswith('META-INF/') and n.endswith('.RSA'):
            res = subprocess.run(['openssl', 'pkcs7', '-inform', 'DER', '-print_certs'], input=z.read(n), capture_output=True)
            res2 = subprocess.run(['openssl', 'x509', '-outform', 'DER'], input=res.stdout, capture_output=True)
            der = res2.stdout
            h = 1
            for b in der:
                h = (31 * h + (b if b < 128 else b - 256)) & 0xffffffff
            print(f'phone_GmsCore cert hash: {h:08x}')
