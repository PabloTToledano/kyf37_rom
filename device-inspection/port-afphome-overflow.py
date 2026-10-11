"""Adapt the single proprietary ActionBar helper call in an isolated app stage."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
path=root/'jp/kyocera/afphome/applist/AppListActivity.smali'
source=path.read_text()
old='    invoke-virtual {v0, v1, v2}, Ljp/kyocera/kcfp/util/KCfpWidgetUtil;->setDisplayShowOverflowMenuButtonEnabled(Landroid/app/ActionBar;Z)V'
new='    move-object v1, p0\n\n    invoke-virtual {v0, v1, v2}, Ljp/kyocera/kcfp/util/KCfpWidgetUtil;->setDisplayShowOverflowMenuButtonEnabled(Landroid/app/Activity;Z)V'
assert source.count(old)==1
path.write_text(source.replace(old,new))
print('Adapted AppListActivity overflow helper to its Activity window')
