from pathlib import Path
import hashlib
p=Path('/home/pablo/kyf37-android10/out/target/product/kyf37/system/media/bootanimation.zip')
print('Installed animation:',p.exists(),hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'not installed yet')
