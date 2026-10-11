import zipfile, subprocess, re

with open('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java') as f:
    text = f.read()

m = re.search(r'MICROG_REAL_SIGNATURE\s*=\s*new Signature\("([0-9a-fA-F]+)"\)', text)
pms_sig = m.group(1).lower()

with zipfile.ZipFile('/home/pablo/microg/com.google.android.gms-252432034.apk') as z:
    for n in z.namelist():
        if n.startswith('META-INF/') and n.endswith('.RSA'):
            res = subprocess.run(['openssl', 'pkcs7', '-inform', 'DER', '-print_certs', '-outform', 'DER'], input=z.read(n), capture_output=True)
            apk_cert = res.stdout.hex().lower()
            print('PMS sig len:', len(pms_sig))
            print('APK cert len in hex:', len(apk_cert))
            print('Exact match?:', pms_sig == apk_cert)
