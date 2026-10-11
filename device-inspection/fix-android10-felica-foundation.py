"""Stage exact stock FeliCa configs/device ownership; never accesses a phone.

Default prepares reviewable files only. --apply requires the shared build lock to
be free, and does not enable wallet APKs, initialize a chip or write /persist.
"""
from pathlib import Path
import argparse,json,re,hashlib,fcntl,shutil
here=Path(__file__).resolve().parent;ws=here.parent
tree=Path('/home/pablo/kyf37-android10');stock=Path('/home/pablo/kyf37-rom/stock-system')
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
out=ws/'kyf37-rom/felica-foundation';out.mkdir(exist_ok=True)
uids=json.loads((ws/'kyf37-rom/felica-stock-uid-candidates.json').read_text())
evidence={x['name']:x['candidate_uid'] for x in uids if x['elf']=='libc.so'}
assert all(evidence.get(k)==v for k,v in {'root':0,'system':1000,'radio':1001,'nfc':1027,'kmfc':9000}.items()),'OEM identity evidence differs'
reference=(here/'recovery-stock/ueventd.rc').read_text()
nodes={'felica_cen','felica_pon','felica','felica_rws','felica_rate','int_poll','felicadev_poll','rfs_poll','felica_rfs','kfelicavbus','vfc_rst','felica_status','felica_ue'}
owners={'root':'0','system':'1000','kmfc':'9000'}
rules=[]
for line in reference.splitlines():
 fields=line.split()
 if len(fields)==4 and fields[0].startswith('/dev/') and fields[0][5:] in nodes:
  path,mode,uid,gid=fields
  assert re.fullmatch(r'0[0-7]{3}',mode)
  rules.append(' '.join([path,mode,owners[uid],owners[gid]]))
assert len(rules)==len(nodes), 'All original device rules are required'
block='# BEGIN KYF37 FeliCa stock device ownership\n'+'\n'.join(rules)+'\n# END KYF37 FeliCa stock device ownership\n'
(out/'ueventd-felica.rules').write_text(block)
configs=[]
for name in ['common.cfg','mfm.cfg','mfs.cfg']:
 source=stock/'etc/felica'/name;target=out/name;shutil.copy2(source,target)
 configs.append({'file':name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size})
report={'kernel_driver_enabled':'CONFIG_KFELICA=y' in Path('/home/pablo/kyf37-rom/kernel-android10-gcc48-build/.config').read_text().splitlines(),
 'stock_identity_evidence':evidence,'configs':configs,'device_rules':rules,'applied':False,'phone_accessed':False,
 'apps_enabled':False,'chip_initialized':False,'persist_modified':False,'payment_ready':False,
 'remaining':['Native kmfc identity + android.uid.felica UID 9000 mapping','Dedicated SELinux app/device/service contexts','Original UART service replacing infrared fallback without duplicate registration','FeliCa client/service native and permission runtime checks','Stock signature/trust/provisioning contracts; hardware communication test']}
if args.apply:
 with Path('/home/pablo/kyf37-build.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  device=tree/'device/kyocera/kyf37';dest=device/'felica';dest.mkdir(exist_ok=True)
  for item in configs:shutil.copy2(out/item['file'],dest/item['file'])
  p=device/'ramdisk/ueventd.qcom.rc';s=p.read_text()
  s=re.sub(r'# BEGIN KYF37 FeliCa stock device ownership\n.*?# END KYF37 FeliCa stock device ownership\n','',s,flags=re.S)
  for path in nodes:
   assert not re.search(r'^/dev/'+re.escape(path)+r'\s',s,re.M),'Existing conflicting rule requires review: '+path
  p.write_text(s.rstrip()+'\n\n'+block)
  p=device/'device.mk';s=p.read_text()
  for item in configs:
   pair='device/kyocera/kyf37/felica/'+item['file']+':system/etc/felica/'+item['file']
   if pair not in s:s+='\nPRODUCT_COPY_FILES += '+pair+'\n'
  p.write_text(s);report['applied']=True
(out/'foundation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Stock configs:',len(configs),'device mappings:',len(rules),'applied:',report['applied'],'hardware verified: false')
