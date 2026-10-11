import subprocess, re, zipfile

with open('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java') as f:
    text = f.read()

m = re.search(r'MICROG_REAL_SIGNATURE\s*=\s*new Signature\("([0-9a-fA-F]+)"\)', text)
pms_sig = bytes.fromhex(m.group(1))

with zipfile.ZipFile('/home/pablo/microg/com.google.android.gms-252432034.apk') as z:
    for n in z.namelist():
        if n.startswith('META-INF/') and n.endswith('.RSA'):
            raw = z.read(n)
            res = subprocess.run(['openssl', 'pkcs7', '-inform', 'DER', '-print_certs'], input=raw, capture_output=True)
            # convert PEM to DER
            res2 = subprocess.run(['openssl', 'x509', '-outform', 'DER'], input=res.stdout, capture_output=True)
            apk_cert = res2.stdout
            print('pms_sig length:', len(pms_sig))
            print('apk_cert length:', len(apk_cert))
            print('Exact byte match?:', pms_sig == apk_cert)
