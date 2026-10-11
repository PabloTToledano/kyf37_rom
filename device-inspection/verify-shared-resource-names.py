from pathlib import Path
import json,zipfile,argparse
from androguard.core.axml import ARSCParser
from loguru import logger
logger.remove()
root=Path('kyf37-rom')
parser=argparse.ArgumentParser()
parser.add_argument('--framework',action='store_true')
args=parser.parse_args()
apk='android-7-framework-res-built.apk' if args.framework else 'shared-resource-compile-check.apk'
aliases=json.loads((root/'afphome-shared-resource-map.json').read_text())['aliases']
with zipfile.ZipFile(root/apk) as z:
    resources=ARSCParser(z.read('resources.arsc'))
package=resources.get_packages_names()[0]
results=[]
for alias,name in aliases['mResName'].items():
    kind=aliases['mResType'][alias]
    rid=resources.get_res_id_by_key(package,kind,name)
    assert rid, (alias,kind,name)
    if args.framework:assert package=='android' and rid>>24==1,(package,hex(rid))
    results.append({'alias':alias,'type':kind,'name':name,'compiled_id':hex(rid)})
report='shared-resource-framework-verification.json' if args.framework else 'shared-resource-name-verification.json'
scope='Built framework resource name resolution; runtime remains unverified.' if args.framework else 'Standalone compilation and name resolution; framework overlay and runtime remain unverified.'
(root/report).write_text(json.dumps({'apk':apk,'package':package,'resources':results,'scope':scope},indent=2)+'\n')
print(f'All {len(results)} shared-resource aliases resolve in the compiled resource package.')
