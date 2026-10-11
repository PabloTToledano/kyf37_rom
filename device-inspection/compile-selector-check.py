from pathlib import Path
import subprocess
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--resources',default='selector-source/res')
parser.add_argument('--output',default='selector-compile-check.apk')
args=parser.parse_args()
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
temp=Path('/home/pablo/kyf37-rom/selector-compile-check')
temp.mkdir(exist_ok=True)
manifest=temp/'AndroidManifest.xml'
manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.selectorcheck"><application/></manifest>')
apk=host/'kyf37-rom'/args.output
subprocess.run(['/home/pablo/kyf37-twrp/prebuilts/sdk/tools/linux/aapt','package','-f',
 '-M',str(manifest),'-S',str(host/'kyf37-rom'/args.resources),
 '-I','/home/pablo/kyf37-lineage/prebuilts/sdk/current/android.jar','-F',str(apk)],check=True)
print('Selector sources compiled successfully:',apk)
