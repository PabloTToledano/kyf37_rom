from pathlib import Path
import shutil
root=Path('/home/pablo/kyf37-android10');stock=Path('/home/pablo/kyf37-rom/stock-system')
p=root/'packages/apps/Kyf37Irda'
p.mkdir(exist_ok=True)
shutil.copy2('/home/pablo/kyf37-rom/irda-compat/IrDATransfer.apk',p/'IrDATransfer.apk')
(p/'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := Kyf37Irda
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := IrDATransfer.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_PRIVILEGED_MODULE := true
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)
''')
files=['bin/irdadaemon','lib/libDc3pIrSimple.so']
p=root/'vendor/kyocera/kyf37/proprietary-files.txt';s=p.read_text()
mk=root/'vendor/kyocera/kyf37/kyf37-vendor.mk';m=mk.read_text()
for f in files:
 dst=root/'vendor/kyocera/kyf37/proprietary'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stock/f,dst)
 if f not in s.splitlines():s+=f+'\n'
 mapping='vendor/kyocera/kyf37/proprietary/'+f+':system/'+f
 if mapping not in m:m+='\nPRODUCT_COPY_FILES += '+mapping+'\n'
p.write_text(s);mk.write_text(m)
p=root/'device/kyocera/kyf37/device.mk';s=p.read_text()
if 'PRODUCT_PACKAGES += Kyf37Irda' not in s:s+='\nPRODUCT_PACKAGES += Kyf37Irda\n'
p.write_text(s)
policy=root/'device/kyocera/kyf37/sepolicy'
print('Policy directory',policy,policy.exists())
(policy/'kyf37_irda.te').write_text('''type kyf37_irda, domain, coredomain;
type kyf37_irda_exec, exec_type, file_type, system_file_type;
init_daemon_domain(kyf37_irda)
# Development ROM remains permissive while stock device/socket accesses are audited.
permissive kyf37_irda;
''')
p=policy/'file_contexts';s=p.read_text()
if '/system/bin/irdadaemon' not in s:s+='\n/system/bin/irdadaemon u:object_r:kyf37_irda_exec:s0\n'
p.write_text(s)
permissions=root/'device/kyocera/kyf37/permissions/privapp-permissions-kyf37-irda.xml'
permissions.parent.mkdir(exist_ok=True)
permissions.write_text('''<permissions><privapp-permissions package="com.kyocera.irda"><permission name="android.permission.WRITE_SECURE_SETTINGS"/></privapp-permissions></permissions>\n''')
p=root/'device/kyocera/kyf37/device.mk';s=p.read_text()
entry='device/kyocera/kyf37/permissions/privapp-permissions-kyf37-irda.xml:system/etc/permissions/privapp-permissions-kyf37-irda.xml'
if entry not in s:s+='\nPRODUCT_COPY_FILES += '+entry+'\n'
p.write_text(s)
print('Original infrared APK, JNI, daemon and privilege/domain setup integrated; hardware transfer untested')
