from pathlib import Path
import hashlib
r=Path('/home/pablo/kyf37-android10/out/target/product/kyf37/system')
for p in r.rglob('bootanimation.zip'):print(p,hashlib.sha256(p.read_bytes()).hexdigest())
