"""Compare preserved live system to the original v2 image, read-only."""
from pathlib import Path
import hashlib,subprocess,json,tempfile,re
root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
live=root/'phone-backup/android10-bootloop-20261007/system-live.raw.img'
original=root/'kyf37-rom/android10-go-candidate-20261007/system-android10.raw.img'
assert live.stat().st_size==original.stat().st_size==1612709888
changed=[]
with original.open('rb') as a,live.open('rb') as b:
    old_head=a.read(4096);new_head=b.read(4096)
    changed_head_bytes=[i for i,(a,b) in enumerate(zip(old_head,new_head)) if a!=b]
with original.open('rb') as a,live.open('rb') as b:
    offset=0
    while True:
        old=a.read(4*1024*1024);new=b.read(4*1024*1024)
        if not old:break
        if old!=new:
            for pos in range(0,len(old),4096):
                if old[pos:pos+4096]!=new[pos:pos+4096]:changed.append((offset+pos)//4096)
        offset+=len(old)
fsck=subprocess.run(['e2fsck','-f','-n',str(live)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(root/'device-inspection/android10-failed-system-e2fsck.txt').write_text(fsck.stdout)
hashes={}
with tempfile.TemporaryDirectory() as temp:
    temp=Path(temp)
    for name in ['/bin/init','/bin/ueventd','/build.prop','/etc/apns-conf.xml','/vendor/etc/selinux/precompiled_sepolicy']:
        pair=[]
        for index,image in enumerate([original,live]):
            out=temp/(str(index)+'.bin')
            stat=subprocess.check_output(['debugfs','-R','stat '+name,str(image)],stderr=subprocess.DEVNULL,text=True)
            if 'Type: symlink' in stat:
                match=re.search(r'Fast link dest: "([^"]+)"',stat);assert match,stat
                pair.append('symlink:'+match.group(1));continue
            subprocess.run(['debugfs','-R','dump '+name+' '+str(out),str(image)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            assert out.exists(),name
            pair.append(hashlib.sha256(out.read_bytes()).hexdigest());out.unlink()
        hashes[name]={'original':pair[0],'live':pair[1],'identical':pair[0]==pair[1]}
report={'changed_4k_blocks':len(changed),'changed_block_numbers_first_100':changed[:100],
        'changed_first_block_byte_offsets':changed_head_bytes,
        'live_filesystem_check_exit':fsck.returncode,'critical_file_hashes':hashes,
        'scope':'Block differences and selected startup files; not a hardware boot success claim'}
(root/'kyf37-rom/android10-failed-system-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
