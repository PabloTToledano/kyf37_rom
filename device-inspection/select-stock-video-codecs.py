from pathlib import Path
tree=Path('/home/pablo/kyf37-lineage')
p=tree/'hardware/qcom/media-caf/msm8916/mm-video-v4l2/Android.mk'
s=p.read_text()
guard='ifneq ($(KYF37_USE_STOCK_VIDEO_CODECS),true)'
if guard not in s:
    assert s.strip()=='OMX_VIDEO_PATH := $(call my-dir)\ninclude $(call all-makefiles-under,$(OMX_VIDEO_PATH))'
    p.write_text('# KYF37 installs model-kernel-compatible proprietary video components.\n'+guard+'\n'+s+'\nendif\n')
# Fail before build if the intended providers are missing from the product.
vendor=(tree/'vendor/kyocera/kyf37/kyf37-vendor.mk').read_text()
for name in ('libOmxVenc.so','libOmxVdec.so'):
    assert ':system/lib/'+name in vendor,name
    assert (tree/'vendor/kyocera/kyf37/proprietary/lib'/name).is_file(),name
print('KYF37 stock video components selected; other devices retain source video modules.')
p=tree/'vendor/qcom/opensource/dataservices/rmnetctl/Android.mk'
s=p.read_text()
guard='ifneq ($(KYF37_USE_STOCK_RMNET),true)'
if guard not in s:
    assert s.strip()=='include $(call all-subdir-makefiles)'
    p.write_text('# KYF37 uses its original kernel-compatible rmnet library.\n'+guard+'\n'+s+'\nendif\n')
assert ':system/lib/librmnetctl.so' in vendor
print('KYF37 stock rmnet provider selected.')
