from pathlib import Path
import shutil, subprocess
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0
tree = Path('/home/pablo/kyf37-android10')
device = tree/'device/kyocera/kyf37'
shutil.copy2(Path(__file__).with_name('filter-android10-kernel-headers.py'),device/'filter-kernel-headers.py')
board = device/'BoardConfig.mk'
if 'KERNEL_HEADERS_POSTPROCESS_CMD :=' not in board.read_text():
    board.write_text(board.read_text()+'\nKERNEL_HEADERS_POSTPROCESS_CMD := python3 device/kyocera/kyf37/filter-kernel-headers.py\n')
config = tree/'vendor/lineage/config/BoardConfigSoong.mk'
s = config.read_text()
if 'KERNEL_HEADERS_POSTPROCESS_CMD ?=' not in s:
    anchor = 'EXPORT_TO_SOONG := \\\n'
    assert s.count(anchor)==1
    s = s.replace(anchor,'KERNEL_HEADERS_POSTPROCESS_CMD ?= true\n\n'+anchor+'    KERNEL_HEADERS_POSTPROCESS_CMD \\\n')
    config.write_text(s)
bp = tree/'vendor/lineage/build/soong/Android.bp'
s = bp.read_text()
if '$(KERNEL_HEADERS_POSTPROCESS_CMD)' not in s:
    anchor = ' headers_install"'
    assert s.count(anchor)==1
    bp.write_text(s.replace(anchor,' headers_install && $(KERNEL_HEADERS_POSTPROCESS_CMD) $(genDir)/usr/include"'))
print('Device-only UAPI filter configured for generated Soong headers.')
