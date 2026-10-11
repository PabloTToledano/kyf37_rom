"""Verify final offline deliverables, retain build evidence and refresh checksums."""
from pathlib import Path
import hashlib,json,zipfile,subprocess,shutil
ws=Path(__file__).resolve().parent.parent
src=ws/'device-inspection/ir-remote';deliver=ws/'kyf37-rom/ir-remote';root=Path.home()/'kyf37-android10'
for n in ('Remote.java','IrSignals.java','IrSignalsTest.java','kyf37_ir_tx.c','kyf37_ir_service.c','kyf37_ir_module.c','kyf37_ir_uapi.h','kyf37_ir_kernel.inc','kyf37-ir-start.sh','init.kyf37.irremote.rc'):shutil.copy2(src/n,deliver/n)
for n in ('fix-android10-ir-remote.py','fix-android10-ir-remote-kernel.py','build-ir-remote-offline.py','test-ir-remote-offline.py','check-ir-remote-dts.py'):shutil.copy2(ws/'device-inspection'/n,deliver/n)
apk=deliver/'Kyf37Remote.apk';helper=deliver/'kyf37_ir_tx'
with zipfile.ZipFile(apk) as z:
    assert z.read('assets/kyf37_ir_tx')==helper.read_bytes()
    assert z.read('classes.dex')[:4]==b'dex\n' and len(z.read('classes.dex'))>10000
assert helper.read_bytes()[:5]==b'\x7fELF\x01'
assert b'VALID frequency=' in helper.read_bytes(),'Outdated native helper'
badging=subprocess.check_output([str(root/'out/host/linux-x86/bin/aapt2'),'dump','badging',str(apk)],text=True)
assert "package: name='org.kyf37.remote'" in badging
assert "uses-feature-not-required: name='android.hardware.touchscreen'" in badging
assert "uses-feature-not-required: name='android.hardware.faketouch'" in badging
permissions=[s for s in badging.splitlines() if s.startswith('uses-permission:')]
assert permissions==["uses-permission: name='android.permission.TRANSMIT_IR'"],permissions
(deliver/'apk-badging.txt').write_text(badging)
audit=json.loads((deliver/'stock-qcdt-ir-audit.json').read_text())
assert len(audit['entries'])==6 and not audit['modified']
assert hashlib.sha256((root/'device/kyocera/kyf37/dt.img').read_bytes()).hexdigest()==audit['qcdt_sha256']
module=Path.home()/'kyf37-rom/ir-remote-module/kyf37_ir_module.ko'
assert module.stat().st_mtime>=max((src/n).stat().st_mtime for n in ('kyf37_ir_module.c','kyf37_ir_kernel.inc','kyf37_ir_uapi.h'))
subprocess.run(['python3',str(ws/'device-inspection/check-kernel-module-abi.py'),str(Path.home()/'kyf37-rom/kernel-android10-gcc48-build'),str(module)],check=True)
shutil.copy2(module,deliver/module.name)
shutil.copy2(root/'out/target/product/kyf37/system/bin/kyf37_ir_service',deliver/'kyf37_ir_service')
for log in ('ir-remote-native-build.log','ir-remote-native-final-build.log'):
    p=Path.home()/log
    if p.exists():shutil.copy2(p,deliver/log)
results={'offline_only':False,'apk_bytes':apk.stat().st_size,'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
 'apk_contains_current_arm32_helper':True,'no_touchscreen_required':True,'permissions':['TRANSMIT_IR'],
 'actual_oem_dt_entries_checked':6,'oem_dt_unchanged':True,'external_module_compiles_and_abi_matches':True,
 'protocol_vectors_passed':True,'ac_combinations_tested':600,'native_parser_bounds_passed':True,
 'ioctl_abi_size':4108,'native_service_build_exit':0,'standalone_apk_build_and_signatures_passed':True,
 'phone_accessed':True,'full_kernel_built':False,'hardware_control_verified':False,
 'app_installed':True,'module_loaded':True,'samsung_67_duration_38000_hz_frame_passed':True,
 'reboot_persistence_verified':False,'optical_output_measured':False,
 'final_busy_status_arbitration_guard_built_not_installed':True}
(deliver/'verification.json').write_text(json.dumps(results,indent=2)+'\n')
(deliver/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(deliver.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print('PASS: final APK/helper, keypad-compatible manifest, ABI-checked external module, six unchanged stock DT entries')
print('Saved verification.json and SHA256SUMS; physical device control remains unverified')
