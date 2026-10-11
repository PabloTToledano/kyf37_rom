"""Restore the stock Qualcomm TFTP namespace as build-generated symlinks."""
from pathlib import Path
import os

device = Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
stock = Path('/home/pablo/kyf37-rom/stock-rfs-extract/rfs')
assert stock.is_dir()
lines = ['# Original KYF37 remote filesystem links required by tftp_server.']
links = sorted(p for p in stock.rglob('*') if p.is_symlink())
assert len(links) == 30
for link in links:
    destination = '$(TARGET_OUT)/rfs/' + str(link.relative_to(stock))
    target = os.readlink(link)
    assert target.startswith(('/firmware', '/persist/', '/data/tombstones/'))
    lines += [destination + ':', '\t@mkdir -p $(dir $@)',
              '\t@ln -sfn ' + target + ' $@',
              'ALL_DEFAULT_INSTALLED_MODULES += ' + destination, '']
fragment = device / 'rfs-layout.mk'
fragment.write_text('\n'.join(lines) + '\n')
makefile = device / 'Android.mk'
content = makefile.read_text()
include = 'include $(LOCAL_PATH)/rfs-layout.mk'
if include not in content:
    makefile.write_text(content + '\n' + include + '\n')
print('30 stock RFS links added to the Android image build')
