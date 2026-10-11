"""Integrate the Japanese One Seg TV stack into the ROM source for the NEXT release (does not build or package anything). WSL; idempotent.

Inputs prepared by modem-investigation/tv-tuner (see its README.md; all offline, OEM code unchanged):
  stock-port/FsDtvApp.apk            reconstructed OEM app jp.co.fsi.fs1seg (unsigned; platform-signed by the build)
  stock-port/backend/system/...      dtvserver, 15 libDtv*/libdtvtuner libraries, media/dtv assets (stock sha256 in stock-port-report.json)
  app/                               new launcher/support checker org.kyf37.tv (English/Spanish, D-pad friendly)

What this script does
  * packages/apps/FsDtvApp (platform cert, ordinary /system/app) and packages/apps/Kyf37Tv (platform cert)
  * copies the backend under device/kyocera/kyf37/tv/ and installs it at the absolute paths the app loads (/system/lib, /system/bin, /system/media/dtv)
  * /system/etc/public.libraries-kyocera.txt so the app's linker namespace may dlopen the TV libraries
  * dtvserver becomes an on-demand service (disabled, started by the launcher) instead of class main: the binary previously
    did not exist; with unresolved Android-5 symbols an auto-started daemon would crash-loop and drain the battery.
Known limitation (README, native-compatibility-audit.json): 62 unresolved imports in libDtv/libDtvULayer/dtvserver (Skia, ICU 53, old GraphicBuffer/AudioTrack),
and One Seg is ISDB-T 1seg (Japan) — Spain broadcasts DVB-T, so no stations are expected. The files are NOT added to proprietary-files.txt, so the
installer's strict vendor-symbol audit does not treat the known-unresolved TV libraries as release blockers.
"""
import os, shutil, stat
from pathlib import Path

src = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/modem-investigation/tv-tuner')
root = Path('/home/pablo/kyf37-android10')
dev = root / 'device/kyocera/kyf37'

# 1. OEM app
fs = root / 'packages/apps/FsDtvApp'
fs.mkdir(parents=True, exist_ok=True)
shutil.copy2(src / 'stock-port/FsDtvApp.apk', fs / 'FsDtvApp.apk')
(fs / 'Android.mk').write_text('''LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := FsDtvApp
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := FsDtvApp.apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := platform
LOCAL_DEX_PREOPT := false
include $(BUILD_PREBUILT)
''')

# 2. New launcher / support checker. Starts the on-demand daemon before opening the OEM app.
tv = root / 'packages/apps/Kyf37Tv'
if tv.exists(): shutil.rmtree(tv)
shutil.copytree(src / 'app', tv)
java = tv / 'src/org/kyf37/tv/TvActivity.java'
code = java.read_text()
marker = 'KYF37 on-demand dtvserver'
if marker not in code:
    code = code.replace('    private void launchTv() {', '''    /** KYF37 on-demand dtvserver: the daemon is not started at boot (see install-tv-oneseg.py); start it when the TV app is opened. */
    private void startBackend() {
        try {
            Class.forName("android.os.SystemProperties").getMethod("set", String.class, String.class)
                    .invoke(null, "ctl.start", "dtvserver");
        } catch (Throwable ignored) { /* needs the platform signature; fall through and let the OEM app report the failure */ }
    }

    private void launchTv() {
        startBackend();''', 1)
    java.write_text(code)
(tv / 'Android.bp').write_text('''android_app {
    name: "Kyf37Tv",
    srcs: ["src/**/*.java"],
    resource_dirs: ["res"],
    sdk_version: "current",
    min_sdk_version: "23",
    certificate: "platform",
    optimize: { enabled: false },
}
''')

# 3. Backend payload
dst = dev / 'tv'
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src / 'stock-port/backend/system', dst / 'system')
lines = []
libs = []
for p in sorted((dst / 'system').rglob('*')):
    if not p.is_file(): continue
    rel = p.relative_to(dst / 'system').as_posix()
    mode = 0o755 if rel == 'bin/dtvserver' else 0o644
    os.chmod(p, mode)
    lines.append(f'device/kyocera/kyf37/tv/system/{rel}:system/{rel}')
    if rel.startswith('lib/') and rel.endswith('.so'): libs.append(rel.split('/')[-1])
public = dev / 'public.libraries-kyocera.txt'
public.write_text('\n'.join(libs) + '\n')
lines.append('device/kyocera/kyf37/public.libraries-kyocera.txt:system/etc/public.libraries-kyocera.txt')
BS, NL = chr(92), chr(10)
(dev / 'tv-oem.mk').write_text('PRODUCT_COPY_FILES += ' + BS + NL + '    ' + (' ' + BS + NL + '    ').join(lines) + NL +
                               'PRODUCT_PACKAGES += FsDtvApp Kyf37Tv' + NL)
dm = dev / 'device.mk'; s = dm.read_text()
inc = '$(call inherit-product, device/kyocera/kyf37/tv-oem.mk)'
if inc not in s: dm.write_text(s.rstrip() + NL + inc + NL)

# 4. dtvserver on demand (the OEM entry was `class main`, auto-start)
rc = dev / 'ramdisk/init.kc.common.rc'
t = rc.read_text()
old = 'service dtvserver /system/bin/dtvserver\n    class main\n'
new = 'service dtvserver /system/bin/dtvserver\n    class main\n    disabled\n    oneshot\n'
if old in t: rc.write_text(t.replace(old, new, 1)); print('dtvserver set to on-demand')
elif 'service dtvserver' in t: print('dtvserver rc already adjusted')
print(len(libs), 'libraries,', len(lines), 'copy entries; app + launcher wired. No build started.')
