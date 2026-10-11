import base64, hashlib, json, urllib.request
from pathlib import Path

url='https://android.googlesource.com/platform/prebuilts/sdk/+/android-10.0.0_r47/29/public/android.jar?format=TEXT'
root=Path('kyf37-rom/android10-reference')
data=base64.b64decode(urllib.request.urlopen(url,timeout=60).read())
assert data[:2]==b'PK', 'Not a JAR'
(root/'android-29.jar').write_bytes(data)
(root/'android-29-provenance.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)},indent=2))
print('Android 29 SDK reference downloaded:',len(data),'bytes')
