"""Stage all missing Qualcomm imaging, algorithm, fastcv, and JPEG libraries for KYF37 camera.
Also allow standard camera app (Snap/Camera2) to be built alongside KyoceraCamera.
WSL; idempotent.
"""
import shutil
from pathlib import Path

root = Path('/home/pablo/kyf37-android10/vendor/kyocera/kyf37')
stock_vlib = Path('/home/pablo/kyf37-rom/stock-system/vendor/lib')
stock_slib = Path('/home/pablo/kyf37-rom/stock-system/lib')

libs_from_vlib = [
    'libCipo_ae.so',
    'libCipo_awb.so',
    'libmmcamera2_frame_algorithm.so',
    'libmmcamera_wavelet_lib.so',
    'libmmcamera_hdr_lib.so',
    'libmmcamera_hdr_gb_lib.so',
    'libmmcamera_faceproc.so',
    'libfastcvopt.so',
    'libjpegdhw.so',
    'libjpegehw.so',
    'libmmjpeg.so',
    'libmmqjpeg_codec.so',
    'libqomx_jpegdec.so',
    'libqomx_jpegenc.so',
]

dest_dir = root / 'proprietary/vendor/lib'
dest_dir.mkdir(parents=True, exist_ok=True)

lst_file = root / 'proprietary-files.txt'
lst_text = lst_file.read_text()

mk_file = root / 'kyf37-vendor.mk'
mk_text = mk_file.read_text()

for lib in libs_from_vlib:
    src_file = stock_vlib / lib
    if src_file.exists():
        shutil.copy2(src_file, dest_dir / lib)
        line = 'vendor/lib/' + lib
        if line not in lst_text.splitlines():
            lst_text = lst_text.rstrip('\n') + '\n' + line + '\n'
        cp = f'PRODUCT_COPY_FILES += vendor/kyocera/kyf37/proprietary/vendor/lib/{lib}:system/vendor/lib/{lib}'
        if cp not in mk_text:
            mk_text = mk_text.rstrip('\n') + '\n' + cp + '\n'

# Also ensure libstlport.so is available in vendor/lib for libmmcamera_hdr_gb_lib.so
stlport = stock_slib / 'libstlport.so'
if stlport.exists():
    shutil.copy2(stlport, dest_dir / 'libstlport.so')
    line = 'vendor/lib/libstlport.so'
    if line not in lst_text.splitlines():
        lst_text = lst_text.rstrip('\n') + '\n' + line + '\n'
    cp = 'PRODUCT_COPY_FILES += vendor/kyocera/kyf37/proprietary/vendor/lib/libstlport.so:system/vendor/lib/libstlport.so'
    if cp not in mk_text:
        mk_text = mk_text.rstrip('\n') + '\n' + cp + '\n'

lst_file.write_text(lst_text)
mk_file.write_text(mk_text)

# Remove package overrides from KyoceraCamera so Snap/Camera2 is also available for testing
app_mk = Path('/home/pablo/kyf37-android10/packages/apps/Kyf37StockApps/Android.mk')
s = app_mk.read_text()
s = s.replace('LOCAL_OVERRIDES_PACKAGES := Snap Camera2 LibreCamera\n', 'LOCAL_OVERRIDES_PACKAGES :=\n')
app_mk.write_text(s)

print(f"Staged {len(libs_from_vlib) + 1} camera vendor libraries and updated proprietary-files.txt and Android.mk")
