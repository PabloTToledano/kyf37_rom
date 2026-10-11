import subprocess

cmd = ['/home/pablo/kyf37-android10/out/host/linux-x86/bin/dexdump', '-d', '/tmp/classes5.dex']
res = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, errors='ignore')

targets = ['RomSpoofSignatureChecks', 'SystemChecks', 'InstalledPackagesChecks', 'PermissionCheckGroup']
capture = False
count = 0
for line in res.stdout:
    if any(f'Class descriptor  : \'Lorg/microg/tools/selfcheck/{t};' in line for t in targets):
        capture = True
        count = 0
        print('----------------------------------------')
        print(line.strip())
    elif capture:
        if line.startswith('Class #'):
            capture = False
        else:
            if 'name          :' in line or 'const-string' in line or 'invoke-virtual' in line or 'invoke-static' in line or 'sget' in line:
                print(' ', line.strip())
