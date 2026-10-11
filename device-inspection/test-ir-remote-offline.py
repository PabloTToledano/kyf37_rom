"""Protocol vectors, native parser bounds, ABI and APK contents; never opens hardware."""
from pathlib import Path
import subprocess,os,zipfile,json
ws=Path(__file__).resolve().parent.parent
src=ws/'device-inspection/ir-remote'
root=Path.home()/'kyf37-android10';out=Path.home()/'kyf37-rom/ir-remote-tests';out.mkdir(exist_ok=True)
jdk=root/'prebuilts/jdk/jdk8/linux-x86/bin'
subprocess.run([str(jdk/'javac'),'-d',str(out),str(src/'IrSignals.java'),str(src/'IrSignalsTest.java')],check=True)
subprocess.run([str(jdk/'java'),'-cp',str(out),'org.kyf37.remote.IrSignalsTest'],check=True)
host=out/'ir-tx-host'
subprocess.run(['gcc','-Wall','-Wextra','-Werror',str(src/'kyf37_ir_tx.c'),'-o',str(host)],check=True)
cases=[('38000 3 0 9000 4500 560',True),('40000 1 3 600',True),
       ('29000 1 0 500',False),('38000 0 0',False),('38000 1025 0',False),
       ('38000 1 4 500',False),('38000 1 0 10001',False),
       ('38000 2 0 560 100001',False),('38000 3 0 560 -1 560',False),
       ('38000 2 0 560',False),
       ('38000 10 0 '+' '.join(['10000','100000']*5),False)]
for inp,valid in cases:
    r=subprocess.run([str(host),'validate'],input=inp,text=True,capture_output=True,timeout=2)
    assert (r.returncode==0)==valid,(inp,r.stdout,r.stderr)
    if valid:assert 'ABI_size=4108' in r.stdout,r.stdout
print('PASS: native parser rejects bad frequency/count/flags/durations/truncation/frame size; ABI=4108')
apk=ws/'kyf37-rom/ir-remote/Kyf37Remote.apk'
if apk.exists():
    with zipfile.ZipFile(apk) as z:
        assert len(z.read('classes.dex'))>10000
        assert z.read('assets/kyf37_ir_tx')[:5]==b'\x7fELF\x01'
    print('PASS: APK contains compiled app and ARM32 transmitter')
print('Host checks only: these checks do not establish optical output or TV/AC response')
