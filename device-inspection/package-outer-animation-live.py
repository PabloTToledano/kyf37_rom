#!/usr/bin/env python3
"""Bundle the matching native library into the data APK, platform-sign for live install."""
from pathlib import Path
import subprocess
import zipfile
appout = Path.home() / 'kyf37-android10/out/target/product/kyf37'
ws = Path(__file__).resolve().parent
out = ws / 'outer-animation'
out.mkdir(exist_ok=True)
source = appout / 'system/priv-app/Kyf37OuterScreen/Kyf37OuterScreen.apk'
native = appout / 'system/lib/libkyf37subdisplay.so'
with zipfile.ZipFile(source) as src, zipfile.ZipFile(out/'outer-unsigned.apk','w') as dst:
    for item in src.infolist():
        if item.filename.startswith(('META-INF/', 'lib/')):
            continue
        dst.writestr(item,src.read(item.filename))
    dst.write(native,'lib/armeabi-v7a/libkyf37subdisplay.so',compress_type=zipfile.ZIP_STORED)
    # Data-app linker namespaces cannot see platform libc++; bundle the matching
    # built runtime for the native library's default Android build dependency.
    dst.write(appout/'system/lib/libc++.so','lib/armeabi-v7a/libc++.so',compress_type=zipfile.ZIP_STORED)
subprocess.run(['bash',str(ws/'sign-test-apk.sh'),str(out/'outer-unsigned.apk'),str(out/'Kyf37OuterScreen-animation.apk')],check=True)
print(out/'Kyf37OuterScreen-animation.apk')
