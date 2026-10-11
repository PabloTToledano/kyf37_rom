"""Stage optional NextFP shared library with its original package-manager name."""
from pathlib import Path
import subprocess,zipfile
def stage(dest):
 r=Path('/home/pablo/kyf37-rom');source=r/'remaining-stock-shared-libraries/com.nextfp.android.util/smali'
 subprocess.run(['/home/pablo/kyf37-host-tools/jdk8/bin/java','-jar',str(r/'tools/smali.jar'),'assemble',str(source),'-o',str(dest/'nextfp.dex')],check=True)
 with zipfile.ZipFile(dest/'com.nextfp.android.util.jar','w',zipfile.ZIP_DEFLATED) as z:z.write(dest/'nextfp.dex','classes.dex')
 (dest/'com.nextfp.android.util.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<permissions><library name="com.nextfp.android.util" file="/system/framework/com.nextfp.android.util.jar" /></permissions>\n')
 return '''include $(CLEAR_VARS)
LOCAL_MODULE := Kyf37NextFpUtil
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := JAVA_LIBRARIES
LOCAL_SRC_FILES := com.nextfp.android.util.jar
LOCAL_MODULE_STEM := com.nextfp.android.util.jar
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := Kyf37NextFpUtilPermissions
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := ETC
LOCAL_SRC_FILES := com.nextfp.android.util.xml
LOCAL_MODULE_STEM := com.nextfp.android.util.xml
LOCAL_MODULE_PATH := $(TARGET_OUT_ETC)/permissions
include $(BUILD_PREBUILT)
'''
