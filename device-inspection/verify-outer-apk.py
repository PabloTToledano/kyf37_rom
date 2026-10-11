from pathlib import Path
import zipfile,json
from loguru import logger
from androguard.core.dex import DEX
logger.remove()
root=Path('kyf37-rom')
apk=root/'Kyf37OuterScreen-built.apk'
with zipfile.ZipFile(apk) as z: data=z.read('classes.dex')
dex=DEX(data)
classes={c.get_name():c for c in dex.get_classes()}
service='Lorg/kyf37/subdisplay/OuterScreenService;'
receiver='Lorg/kyf37/subdisplay/WakeReceiver;'
assert service in classes and receiver in classes,('Missing manifest components',list(classes))
native=[m for m in classes[service].get_methods() if m.get_name()=='updatePanel']
assert len(native)==1 and 'native' in native[0].get_access_flags_string()
assert native[0].get_descriptor().replace(' ','')=='(ZIII)I'
(root/'outer-apk-verification.json').write_text(json.dumps({'classes':sorted(classes),
 'native_method':native[0].get_descriptor(),'dex_bytes':len(data),
 'scope':'Packaged service/receiver and JNI declaration only; runtime remains unverified.'},indent=2)+'\n')
print('Outer service, receiver, and native method are present in packaged DEX.')
