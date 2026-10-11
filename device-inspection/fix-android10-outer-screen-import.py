from pathlib import Path
import subprocess
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java')
s=p.read_text()
line='import android.content.ComponentName;\n'
if line not in s:
    marker='import android.content.Context;\n';assert marker in s
    p.write_text(s.replace(marker,line+marker,1))
print('Outer-screen explicit service ComponentName import added.')
