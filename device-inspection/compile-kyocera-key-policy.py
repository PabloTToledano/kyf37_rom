from pathlib import Path
import subprocess,json
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
stage=host/'kyf37-rom/kyocera-compat/policy-source'
libraries=Path('/home/pablo/kyf37-lineage/out/target/common/obj/JAVA_LIBRARIES')
boot=':'.join(str(libraries/(name+'_intermediates/classes.jar')) for name in ['framework','core-oj','core-libart'])
classpath=':'.join(str(p) for p in libraries.glob('*/classes.jar'))
out=Path('/home/pablo/kyf37-rom/kyocera-compat/policy-classes');out.mkdir(parents=True,exist_ok=True)
command=['/home/pablo/kyf37-host-tools/jdk8/bin/javac','-source','8','-target','8','-bootclasspath',boot,'-classpath',classpath,'-d',str(out),str(stage/'Kyf37Navigation.java'),str(stage/'PhoneWindowManager.java')]
result=subprocess.run(command,capture_output=True,text=True)
(stage/'compile.log').write_text(result.stdout+result.stderr)
report=json.loads((stage/'verification.json').read_text())
report['compiled']=result.returncode==0
report['javac_exit_code']=result.returncode
report['compile_scope']='Two staged policy Java sources against existing Android7/Lineage build classes; no complete ROM build or DEX verification'
(stage/'verification.json').write_text(json.dumps(report,indent=2))
print('Policy compile exit:',result.returncode)
print((result.stdout+result.stderr)[:3500])
raise SystemExit(result.returncode)
