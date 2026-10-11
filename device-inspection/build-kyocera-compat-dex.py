"""Assemble the stock Kyocera framework helper classes (kcfp/kerr/...) into one dex that ported stock apps carry as classes2.dex. WSL."""
import subprocess, shutil
from pathlib import Path
r = Path('/home/pablo/kyf37-rom'); src = r/'vendor-framework-smali'
jdk = Path('/home/pablo/kyf37-host-tools/jdk8/bin/java')
stage = r/'kyocera-compat-stage'; shutil.rmtree(stage, ignore_errors=True)
for rel in ['jp/kyocera/kcfp', 'jp/kyocera/kerr', 'jp/kyocera/android', 'jp/kyocera/sublcd', 'jp/kyocera/internal', 'jp/kyocera/net']:
    d = src/rel
    if d.is_dir(): shutil.copytree(d, stage/rel)
out = r/'kyocera-compat.dex'
p = subprocess.run([str(jdk), '-jar', str(r/'tools/smali.jar'), 'assemble', str(stage), '-o', str(out)], capture_output=True, text=True)
print(p.returncode, p.stderr[-1500:], out.stat().st_size if out.exists() else None)
