"""Read the actual packaged services.jar; assert all physical-feedback hooks."""
from pathlib import Path
import zipfile,json,hashlib
from loguru import logger
from androguard.core.dex import DEX
logger.remove()
root=Path('kyf37-rom')
jar=root/'services-feedback-built.jar'
with zipfile.ZipFile(jar) as archive:
    data=archive.read('classes.dex')
dex=DEX(data)
classes={c.get_name():c for c in dex.get_classes()}
feedback='Lcom/android/server/policy/Kyf37Feedback;'
assert feedback in classes,'Feedback class not packaged'
policy=classes['Lcom/android/server/policy/PhoneWindowManager;']
calls={}
for method in policy.get_methods():
    if not method.get_code():continue
    for instruction in method.get_instructions():
        if instruction.get_name().startswith('invoke-') and feedback in instruction.get_output():
            calls.setdefault(method.get_name(),[]).append(instruction.get_output())
required={'init':['-><init>','->userChanged'],
          'setCurrentUserLw':['->userChanged'],
          'interceptKeyBeforeQueueing':['->key'],
          'notifyLidSwitchChanged':['->lidChanged']}
for method,targets in required.items():
    for target in targets:
        assert any(target in call for call in calls.get(method,[])),(method,target,calls)
report={'jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
        'policy_calls':calls,'dex_bytes':len(data),
        'scope':'Packaged feedback class and policy call sites only; playback, settings, suppression and hardware remain runtime tests.'}
(root/'feedback-dex-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Feedback class and all four policy integration sites verified in packaged services.jar.')
