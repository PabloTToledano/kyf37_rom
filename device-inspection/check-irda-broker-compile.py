from pathlib import Path
import subprocess
r=Path('/home/pablo/kyf37-android10')
p=r/'out/target/common/obj/JAVA_LIBRARIES/framework_intermediates/classes.jar'
print('Framework classes available',p.exists())
if p.exists():
 out=Path('/home/pablo/kyf37-rom/irda-broker-compile-check');out.mkdir(exist_ok=True)
 subprocess.run(['/home/pablo/kyf37-host-tools/jdk8/bin/javac','-source','8','-target','8','-classpath',str(p),'-d',str(out),str(r/'frameworks/base/services/core/java/com/android/server/policy/Kyf37UartBroker.java')],check=True)
 print('UART broker Java API compile passed')

