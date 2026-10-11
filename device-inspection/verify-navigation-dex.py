from pathlib import Path
import json
from loguru import logger
from androguard.core.dex import DEX
logger.remove()
root=Path('kyf37-rom')
dex=DEX((root/'services-core-built.dex').read_bytes())
classes={c.get_name():c for c in dex.get_classes()}
nav='Lcom/android/server/policy/Kyf37Navigation;'
assert nav in classes
policy=classes['Lcom/android/server/policy/PhoneWindowManager;']
calls={}
for method in policy.get_methods():
 if not method.get_code():continue
 for instruction in method.get_instructions():
  if instruction.get_name().startswith('invoke-') and nav in instruction.get_output():
   calls.setdefault(method.get_name(),[]).append(instruction.get_output())
required={'init','interceptKeyBeforeDispatching','finishedGoingToSleep','notifyLidSwitchChanged','setCurrentUserLw'}
assert required<=calls.keys(),required-calls.keys()
report={'class':nav,'policy_calls':calls,'scope':'Compiled navigation class and policy hooks; actual key/cursor behavior on new ROM remains unverified.'}
(root/'navigation-dex-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Navigation class and all five policy integration hooks verified in built DEX.')
