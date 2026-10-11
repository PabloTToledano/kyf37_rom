"""Verify the installed build assets, not merely the device source copies."""
from pathlib import Path
import argparse,hashlib,json
parser=argparse.ArgumentParser()
parser.add_argument('--tree',default='/home/pablo/kyf37-lineage')
parser.add_argument('--report',type=Path)
args=parser.parse_args()
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
stock=Path('/home/pablo/kyf37-rom/stock-system/media/audio/ui')
built=Path(args.tree)/'out/target/product/kyf37/system/media/audio/ui'
report={};failures=[]
for source in sorted(stock.iterdir()):
    if not source.is_file():continue
    target=built/source.name
    expected=hashlib.sha256(source.read_bytes()).hexdigest()
    actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    report[source.name]={'stock_sha256':expected,'built_sha256':actual,'matches':actual==expected}
    if actual!=expected:failures.append(source.name)
(args.report or host/'built-ui-sound-verification.json').write_text(json.dumps({
    'assets':report,'failures':failures,
    'scope':'Installed build directory recording bytes only; image content and playback require separate verification.'},indent=2)+'\n')
assert not failures,failures
print('All',len(report),'OEM UI recordings match installed build assets.')
