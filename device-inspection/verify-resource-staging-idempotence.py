"""Regression check: identical OEM resource staging must not touch build inputs."""
from pathlib import Path
import hashlib, json, subprocess, sys
root = Path(__file__).resolve().parent.parent
source = root/'kyf37-rom/all-stock-app-ports/resource-decoded/res'
dest = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/overlay/frameworks/base/core/res/res')
paths = [dest/p.relative_to(source) for p in source.rglob('*') if p.is_file()]
paths.append(dest/'values/kyf37_remaining_stock_additions.xml')
def snapshot():
    return {str(p):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in paths}
before = snapshot()
for unused in range(2):
    subprocess.run([sys.executable,str(root/'device-inspection/fix-android10-remaining-stock-resources.py')],check=True)
    assert snapshot() == before, 'Unchanged staging changed resource content or timestamp'
report = {'passed':True,'files_checked':len(paths),'runs':2,'content_and_mtimes_preserved':True}
(root/'kyf37-rom/v22-resource-staging-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
