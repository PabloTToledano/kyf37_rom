"""Preserve the exact device's RIL library selection and startup arguments."""
from pathlib import Path
import subprocess
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0, 'Pause build before changing product properties'
tree=Path('/home/pablo/kyf37-android10')
stock=Path('/home/pablo/kyf37-rom/stock-system/build.prop')
original={}
for line in stock.read_text().splitlines():
    if line.strip() and not line.startswith('#') and '=' in line:
        key,value=line.split('=',1)
        original[key]=value
assert original['rild.libpath']=='/system/vendor/lib/libril-qc-qmi-1.so'
assert original['rild.libargs']=='-d /dev/smd0'
mk=tree/'device/kyocera/kyf37/device.mk'
marker='# Exact KYF37 stock RIL bootstrap (both property APIs)'
if marker not in mk.read_text():
    # Make treats whitespace as property separators; quote the libargs value
    # exactly as product property lists conventionally do for argument strings.
    text='\n'+marker+'\nPRODUCT_PROPERTY_OVERRIDES += \\\n'
    keys=['rild.libpath','ro.telephony.default_network','ril.subscription.types']
    props=[key+'='+original[key] for key in keys]
    props+=['vendor.rild.libpath='+original['rild.libpath']]
    # init sets multiword argument properties; PRODUCT_PROPERTY_OVERRIDES
    # cannot reliably represent them as a whitespace-delimited Make list.
    text+=' \\\n'.join('    '+prop for prop in props)+'\n'
    mk.write_text(mk.read_text()+text)
rc=tree/'device/kyocera/kyf37/ramdisk/init.qcom.rc'
marker='# KYF37 RIL arguments retained from the stock build'
if marker not in rc.read_text():
    rc.write_text(rc.read_text()+'\n'+marker+'\non init\n    setprop rild.libargs "-d /dev/smd0"\n    setprop vendor.rild.libargs "-d /dev/smd0"\n')
print('Exact RIL path, arguments, stock network mode and subscription types staged; hardware telephony unverified.')
