from pathlib import Path
import subprocess,hashlib,json,shutil,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--build-dir',type=Path,default=Path('/home/pablo/kyf37-rom/kernel-android10-gcc48-build'))
args=parser.parse_args()
base=Path('/home/pablo/kyf37-rom')
kernel=base/'kernel-android10';output=args.build_dir
device=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37')
image=output/'arch/arm/boot/zImage'
config=subprocess.check_output([str(kernel/'scripts/extract-ikconfig'),str(image)],text=True)
for required in ['CONFIG_MEMCG=y','CONFIG_MEMCG_SWAP=y','CONFIG_SECCOMP_FILTER=y','CONFIG_ANDROID_BINDER_IPC_32BIT=y','CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"']:
 assert required in config
assert image.stat().st_mtime>(kernel/'security/selinux/nlmsgtab.c').stat().st_mtime
shutil.copy2(image,device/'kernel')
vendor=Path('/home/pablo/kyf37-android10/vendor/kyocera/kyf37/proprietary')
modules={p.name:p for p in output.rglob('*.ko')}
replaced=[];unmatched=[]
for target in (vendor/'lib/modules').rglob('*.ko'):
 source=modules.get(target.name)
 if source:
  shutil.copy2(source,target);replaced.append(str(target.relative_to(vendor)))
 else:unmatched.append(str(target.relative_to(vendor)))
report={'kernel_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'kernel_bytes':image.stat().st_size,
 'embedded_config_requirements_verified':True,'selinux_policy_version_source_max':30,
 'matching_rebuilt_modules':replaced,'stock_modules_without_rebuilt_replacement':unmatched,
 'runtime_verified':False,'warning':'Unmatched stock module CRC compatibility must be audited; no force loading is configured.'}
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
(host/'android10-kernel-staging.json').write_text(json.dumps(report,indent=2));(host/'android10-kernel-config.txt').write_text(config)
(host/'kernel-android10-backports.patch').write_bytes(subprocess.check_output(['git','-C',str(kernel),'diff','--binary']))
print(json.dumps(report,indent=2))
