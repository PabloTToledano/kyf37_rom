"""Run installer control flow against temporary files, never block devices."""
from pathlib import Path
import hashlib, tempfile, subprocess, os, zipfile, json
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
template=(root/'device-inspection/twrp-android10-update-binary.sh').read_text()
sha=lambda b:hashlib.sha256(b).hexdigest()
results={}
with tempfile.TemporaryDirectory(prefix='kyf37-installer-tests-') as temporary:
    base=Path(temporary)
    for case in ['success','check-only','wrong-model','wrong-keystore','corrupt-payload','no-space','mounted-alias','system-write-failure','system-readback-failure']:
        folder=base/case;folder.mkdir(); blocks=folder/'blocks';blocks.mkdir();sd=folder/'sd';sd.mkdir()
        tools=folder/'tools';tools.mkdir();sysfs=folder/'sysfs';sysfs.mkdir()
        originals={}
        for part in ['boot','system','recovery','keystore','modem','modemst1','modemst2','fsg','persist']:
            originals[part]=('original-'+part).encode()*100
            (blocks/part).write_bytes(originals[part])
        # Live KYF37 sysfs: boot p10 starts 151552; recovery p11 starts 184320.
        for part,start,dev in [('mmcblk0p10','151552','179:10'),('mmcblk0p15','290816','179:15')]:
            (sysfs/part).mkdir();(sysfs/part/'start').write_text(start);(sysfs/part/'dev').write_text(dev)
        (folder/'mounts').write_text('/dev/block/mmcblk1p1 '+str(sd)+' vfat rw 0 0\n')
        (folder/'mountinfo').write_text('1 0 '+('179:15' if case=='mounted-alias' else '179:33')+' / /alias rw - ext4 x rw\n')
        boot=b'new-signed-boot'*1024;system=b'new-ext4-system'*4096
        wp=b'#!/bin/sh\nprintf "%s\\n" "$1" >> "$TESTROOT/wp-called"\n'
        package=folder/'rom.zip'
        with zipfile.ZipFile(package,'w') as z:
            z.writestr('boot.img',boot);z.writestr('system.raw.img',system if case!='corrupt-payload' else b'broken')
            z.writestr('tools/clear-system-temp-wp',wp);z.writestr('tools/clear-recovery-boot-temp-wp',wp)
        script=template.replace('BB=/sbin/busybox','BB='+str(tools/'busybox')).replace('BLOCK=/dev/block/bootdevice/by-name','BLOCK='+str(blocks))
        script=script.replace('SYSFS=/sys/class/block','SYSFS='+str(sysfs)).replace('MOUNTINFO=/proc/self/mountinfo','MOUNTINFO='+str(folder/'mountinfo'))
        script=script.replace('SD=/external_sd','SD='+str(sd)).replace('done < /proc/mounts','done < '+str(folder/'mounts'))
        script=script.replace('WORK=/tmp/kyf37-android10-install-$$','WORK='+str(folder/'work')+'-$$')
        # Only fixture copies replace block-device assertions and payload constants.
        script=script.replace('[ -b "$BLOCK/$part" ]','[ -f "$BLOCK/$part" ]')
        replacements={'BOOT_HASH':sha(boot),'SYSTEM_HASH':sha(system),'RECOVERY_HASH':sha(originals['recovery']),
                      'KEYSTORE_HASH':sha(originals['keystore']),'BOOT_BYTES':str(len(boot)),'SYSTEM_BYTES':str(len(system))}
        for key,value in replacements.items():
            line=next(line for line in script.splitlines() if line.startswith(key+'='))
            script=script.replace(line,key+'='+value)
        script=script.replace('@SYSTEM_WP_SHA@',sha(wp)).replace('@BOOT_WP_SHA@',sha(wp))
        (folder/'installer').write_text(script)
        (tools/'getprop').write_text('#!/bin/sh\ncase "$1" in\nro.product.model) echo "${MODEL:-KYF37}";;\nro.serialno) echo 981108631314;;\nro.twrp.version) echo 3.7.0_9-0;;\nesac\n')
        # Every mocked dd path must resolve into this temporary directory.
        (tools/'busybox').write_text('''#!/usr/bin/python3
import os,sys,subprocess,pathlib
r=pathlib.Path(os.environ['TESTROOT']);cmd=sys.argv[1];args=sys.argv[2:]
if cmd=='id':print('0');sys.exit(0)
if cmd=='readlink':
 p=args[-1]
 print('/dev/block/mmcblk0p10' if p.endswith('/blocks/boot') else '/dev/block/mmcblk0p15' if p.endswith('/blocks/system') else p)
 sys.exit(0)
if cmd=='mountpoint':sys.exit(0 if args[-1]==str(r/'sd') else 1)
if cmd=='blockdev':print(os.environ['BOOT_SIZE'] if args[-1].endswith('/boot') else os.environ['SYSTEM_SIZE']);sys.exit(0)
if cmd=='df':print('Filesystem 1024-blocks Used Available Capacity Mounted on\\nfixture 4000000 0 '+os.environ.get('FREE','4000000')+' 0% /fixture');sys.exit(0)
if cmd=='dd':
 for arg in args:
  if arg.startswith(('if=','of=')):
   assert pathlib.Path(arg[3:]).resolve().is_relative_to(r.resolve()), 'NON-FIXTURE DD REFUSED'
 target=next((a[3:] for a in args if a.startswith('of=')),'')
 if target==str(r/'blocks/system'):
  if os.environ.get('FAIL_WRITE'):sys.exit(1)
  if os.environ.get('CORRUPT_WRITE'):
   pathlib.Path(target).write_bytes(b'bad readback');sys.exit(0)
sys.exit(subprocess.run([cmd]+args).returncode)
''')
        for tool in tools.iterdir():tool.chmod(0o755)
        env=dict(os.environ,TESTROOT=str(folder),PATH=str(tools)+':'+os.environ['PATH'],BOOT_SIZE=str(len(boot)),SYSTEM_SIZE=str(len(system)))
        if case=='wrong-model':env['MODEL']='other-phone'
        if case=='wrong-keystore':(blocks/'keystore').write_bytes(b'wrong-owner')
        if case=='no-space':env['FREE']='10'
        if case=='system-write-failure':env['FAIL_WRITE']='1'
        if case=='system-readback-failure':env['CORRUPT_WRITE']='1'
        before={p.name:p.read_bytes() for p in blocks.iterdir()}
        args=['sh',str(folder/'installer'),'3','1',str(package)]
        if case=='check-only':args.append('--check-only')
        result=subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if case in ['success','check-only']:assert result.returncode==0,(case,result.stdout,result.stderr)
        else:assert result.returncode!=0,(case,result.stdout)
        for part in ['recovery','keystore','modem','modemst1','modemst2','fsg','persist']:
            assert (blocks/part).read_bytes()==before[part],(case,part)
        if case=='success':
            assert (blocks/'boot').read_bytes()==boot and (blocks/'system').read_bytes()==system
            backups=list(sd.glob('KYF37-Android10-rollback-*'));assert len(backups)==1
            for part in ['boot','system']:assert (backups[0]/(part+'.img')).read_bytes()==originals[part]
        elif case in ['system-write-failure','system-readback-failure']:
            assert (blocks/'boot').read_bytes()==originals['boot']
            assert 'do not reboot' in result.stdout
        else:
            assert all(p.read_bytes()==before[p.name] for p in blocks.iterdir())
            assert not (folder/'wp-called').exists()
        results[case]='passed'
report={'tests':results,'scope':'Host shell flow with temporary-file fixtures and mocked recovery commands; no phone or block devices accessed.'}
(root/'kyf37-rom/android10-twrp-installer-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
