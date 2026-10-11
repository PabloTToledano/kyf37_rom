"""Port selected original Kyocera apps (deodexed dex + stock resources) into the Android 10 source tree."""
import zipfile, shutil, json
from pathlib import Path
home=Path('/home/pablo')
stock=home/'kyf37-rom/stock-system'
dex_root=home/'kyf37-rom/deoptimized-apps'
dst=home/'kyf37-android10/packages/apps/Kyf37StockApps'
shutil.rmtree(dst,ignore_errors=True); dst.mkdir(parents=True)
APPS=[('KyoceraCamera','priv-app'),('MemoPad','app'),('MemoPadProvider','priv-app'),
      ('MobileLight','app'),('kc_soundrecorder','priv-app'),('kc_soundrecorder_manager','app'),
      ('Reader','priv-app')]
mk=['LOCAL_PATH := $(call my-dir)\n']
names=[]
report={}
for name,base in APPS:
    src_dir=stock/base/name
    apk=src_dir/(name+'.apk')
    dex=dex_root/base/name/(name+'.dex')
    if not dex.exists():
        dex=next((dex_root/base/name).glob('*.dex'))
    out=dst/(name+'.apk')
    with zipfile.ZipFile(apk) as zin, zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as zout:
        have=set()
        for info in zin.infolist():
            if info.filename.startswith('META-INF/') or info.filename.endswith('.dex'): continue
            zout.writestr(info,zin.read(info.filename)); have.add(info.filename)
        zout.write(dex,'classes.dex')
        compat=home/'kyf37-rom/kyocera-compat.dex'
        if compat.exists(): zout.write(compat,'classes2.dex')
        libdir=src_dir/'lib/arm'
        if libdir.is_dir():
            for so in libdir.glob('*.so'):
                n='lib/armeabi-v7a/'+so.name
                if n not in have: zout.write(so,n)
    names.append(name)
    report[name]={'apk':str(apk),'dex':str(dex),'bytes':out.stat().st_size}
    mk.append(f'''include $(CLEAR_VARS)
LOCAL_MODULE := {name}
LOCAL_MODULE_TAGS := optional
LOCAL_OVERRIDES_PACKAGES := {'Snap Camera2 LibreCamera' if name=='KyoceraCamera' else ''}
LOCAL_SRC_FILES := {name}.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := platform
LOCAL_DEX_PREOPT := false
LOCAL_USE_AAPT2 := false
LOCAL_PREBUILT_JNI_LIBS :=
include $(BUILD_PREBUILT)
''')
# Shared Java libraries used by the original camera
for lib,jar in [('jp.kyocera.android.hardware.KCCameraEx','jp.kyocera.android.hardware.KCCameraEx.jar'),
                ('jp.kyocera.morpho.rapideffect.api.EffectManager','jp.kyocera.morpho.rapideffect.api.EffectManager.jar')]:
    shutil.copy2(home/'camera_integration_staging'/jar,dst/jar)
    xml=(stock/'etc/permissions'/(lib+'.xml')).read_text()
    (dst/(lib+'.xml')).write_text(xml)
    mk.append(f'''include $(CLEAR_VARS)
LOCAL_MODULE := {lib}
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := {jar}
LOCAL_MODULE_CLASS := JAVA_LIBRARIES
LOCAL_MODULE_SUFFIX := .jar
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := {lib}.xml
LOCAL_MODULE_CLASS := ETC
LOCAL_MODULE_PATH := $(TARGET_OUT_ETC)/permissions
LOCAL_SRC_FILES := {lib}.xml
include $(BUILD_PREBUILT)
''')
    names += [lib,lib+'.xml']
(dst/'Android.mk').write_text('\n'.join(mk))
(dst/'packages.txt').write_text(' '.join(names))
print(json.dumps(report,indent=1)); print('PRODUCT_PACKAGES +=',' '.join(names))
