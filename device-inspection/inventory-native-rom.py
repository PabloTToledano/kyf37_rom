from pathlib import Path
import subprocess,re,json,hashlib
root=Path('/home/pablo/kyf37-rom/stock-system');out=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
elf={};byname={}
for base in ['lib','vendor/lib','bin','vendor/bin']:
 for p in (root/base).rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  with p.open('rb') as f: magic=f.read(4)
  if magic!=b'\x7fELF':continue
  r=subprocess.run(['readelf','-dW',str(p)],capture_output=True,text=True)
  needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',r.stdout)
  rel=str(p.relative_to(root));elf[rel]={'needed':needed,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};byname.setdefault(p.name,[]).append(rel)
platform=set('libc.so libm.so libdl.so liblog.so libz.so libcutils.so libutils.so libbinder.so libhardware.so libhardware_legacy.so libui.so libgui.so libsync.so libEGL.so libGLESv1_CM.so libGLESv2.so libandroid_runtime.so libnativehelper.so libart.so libstdc++.so libstlport.so libselinux.so libcrypto.so libssl.so libnetutils.so libmedia.so libstagefright.so libstagefright_foundation.so libcamera_client.so libandroid.so libexpat.so libjpeg.so libpng.so libicuuc.so libicui18n.so'.split())
roots=[x for x in elf if x.startswith(('lib/hw/','vendor/lib/hw/','vendor/lib/egl/','lib/egl/')) or Path(x).name in ['rild','qmuxd','netmgrd','qseecomd','wcnss_service','cnss-daemon','sensors.qcom','adsprpcd','rmt_storage','tftp_server','irsc_util','qcom-system-daemon','pm-service','thermal-engine','time_daemon','audiod','mm-qcamera-daemon','perfd','disp_ctrl','kfbmpower','uimd','sensors_fwup','leds_ctrl','akscd','kflcd','libril-qc-qmi-1.so','libril-qcril-hook-oem.so'] or Path(x).name.startswith('libOmx')]
# Bluetooth controller integration is loaded by name, not recorded in DT_NEEDED.
roots.extend(x for x in elf if Path(x).name=='libbt-vendor.so')
seen=set();missing=set();required_platform=set();queue=list(roots)
while queue:
 x=queue.pop()
 if x in seen:continue
 seen.add(x)
 for n in elf[x]['needed']:
  if n in platform:required_platform.add(n);continue
  paths=byname.get(n,[])
  if not paths:missing.add(n)
  else:queue.extend(paths)
report={'roots':roots,'proprietary_dependency_candidates':sorted(seen),'platform_libraries_requiring_ABI_check':sorted(required_platform),'missing_libraries':sorted(missing),'elf':elf,'note':'Dependency candidates only: default HALs and Android platform replacements require review before product inclusion. Not a compatibility claim.'}
(out/'stock-native-dependencies.json').write_text(json.dumps(report,indent=2))
print('ELF files',len(elf),'candidate closure',len(seen),'missing',sorted(missing))
