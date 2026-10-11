from pathlib import Path
import argparse,json,re
parser=argparse.ArgumentParser();parser.add_argument('paths',nargs='+');args=parser.parse_args()
tree=Path('/home/pablo/kyf37-android10')
p=tree/'vendor/kyocera/kyf37/kyf37-vendor.mk';text=p.read_text()
inventory=tree/'vendor/kyocera/kyf37/proprietary-files.txt';paths=inventory.read_text().splitlines()
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
report_path=host/'android10-platform-library-selections.json'
report=json.loads(report_path.read_text()) if report_path.exists() else {}
for relative in args.paths:
 assert relative.startswith('lib/') and relative.endswith('.so') and '..' not in relative
 token='vendor/kyocera/kyf37/proprietary/'+relative+':system/'+relative
 assert text.count(token)==1,(relative,text.count(token))
 text=text.replace(token,'')
 paths.remove(relative)
 report[relative]={'provider':'Android10/Lineage source build','reason':'Stock copy conflicts with selected platform installation; symbol/layout/behavior audit still required'}
p.write_text(text);inventory.write_text('\n'.join(paths)+'\n')
report_path.write_text(json.dumps(report,indent=2))
print('Selected target platform providers for:',args.paths)
