"""Isolated test port of stock Dialer; never replaces current default until verified."""
from pathlib import Path
import subprocess,zipfile,shutil,struct,runpy,json,re
r=Path('/home/pablo/kyf37-rom'); root=Path('/home/pablo/kyf37-android10')
stage=r/'stock-dialer-port';stage.mkdir(exist_ok=True)
java=Path('/home/pablo/kyf37-host-tools/jdk8/bin/java')
def run(*args):subprocess.run([str(x) for x in args],check=True)
compat=runpy.run_path(str(Path(__file__).with_name('stock-resource-compat.py')))
ids=compat['framework_map'](r/'stock-system/framework/framework-res.apk',root/'out/target/product/kyf37/system/framework/framework-res.apk',root/'out/host/linux-x86/bin/aapt2')
(stage/'resource-id-map.json').write_text(json.dumps({hex(k):hex(v) for k,v in ids.items()},indent=1))
legacy=stage/'legacy-framework-smali';legacy.mkdir(exist_ok=True)
for name in ['framework-classes2','telephony-common']:
 dex=r/f'stock-system/framework/arm/boot.oat-dex/{name}.dex'
 if dex.exists():run(java,'-jar',r/'tools/baksmali.jar','disassemble',dex,'-o',legacy)
deopt=stage/'customvcard-deopt';deopt.mkdir(exist_ok=True)
run(java,'-jar',r/'tools/oat2dex.jar','-o',deopt,r/'stock-system/framework/arm/android.pim.customvcard.odex',r/'stock-system/framework/arm/boot.oat-dex')
for dex in deopt.rglob('*.dex'):run(java,'-jar',r/'tools/baksmali.jar','disassemble',dex,'-o',legacy)
smali=stage/'smali'
if smali.exists():shutil.rmtree(smali)
run(java,'-jar',r/'tools/baksmali.jar','disassemble',r/'deoptimized-apps/priv-app/Dialer/Dialer.dex','-o',smali)
for p in smali.rglob('*.smali'):
 s=p.read_text().replace('"com.android.dialer.provider"','"org.kyf37.dialerxx.provider"')
 p.write_text(s)
# Bundle only OEM/legacy classes absent from Android 10, never overwrite boot classes.
known=set()
for p in smali.rglob('*.smali'):
 m=re.search(r'^\.class[^\n]*? L([^;]+);',p.read_text(),re.M)
 if m:known.add(m[1])
for p in (r/'kyocera-compat-stage').rglob('*.smali'):
 m=re.search(r'^\.class[^\n]*? L([^;]+);',p.read_text(),re.M)
 if m:known.add(m[1])
for module in ['framework','telephony-common','voip-common','ims-common','core-oj','core-libart','ext']:
 p=root/f'out/target/common/obj/JAVA_LIBRARIES/{module}_intermediates/classes.jar'
 if p.exists():
  with zipfile.ZipFile(p) as z:known.update(n[:-6] for n in z.namelist() if n.endswith('.class'))
added=[]
queue=list(smali.rglob('*.smali'))
while queue:
 p=queue.pop();text=p.read_text()
 for cls in re.findall(r'L((?:android|com/android|jp/kyocera)/[^;\s<]+);',text):
  if cls in known:continue
  candidate=next((folder/(cls+'.smali') for folder in [legacy,r/'vendor-framework-smali',r/'kc-framework-smali',r/'base-framework-smali'] if (folder/(cls+'.smali')).is_file()),None)
  if candidate is None:continue
  out=smali/(cls+'.smali');out.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(candidate,out);known.add(cls);added.append(cls);queue.append(out)
for p in smali.rglob('*.smali'):
 text=p.read_text()
 text=re.sub(r'(?<![\w])0x1[0-9a-fA-F]{6}(?![\w])',lambda m:hex(ids.get(int(m.group(),16),int(m.group(),16))),text)
 p.write_text(text)
(stage/'bundled-legacy-classes.json').write_text(json.dumps(sorted(added),indent=2))
run('python3',Path(__file__).with_name('fix-android10-stock-call-apis.py'))
run(java,'-jar',r/'tools/smali.jar','assemble',smali,'-o',stage/'classes.dex')
def patch_manifest(data):
 pos=8
 while pos<len(data):
  kind,header,size=struct.unpack_from('<HHI',data,pos)
  if kind!=1:pos+=size;continue
  count,styles,flags,start,styleStart=struct.unpack_from('<5I',data,pos+8)
  assert styles==0, 'Styled manifest string pool unsupported'
  utf8=bool(flags&256); strings=[]
  def length(at):
   if utf8:
    x=data[at];return ((x&127)<<8|data[at+1],at+2) if x&128 else (x,at+1)
   x=struct.unpack_from('<H',data,at)[0];assert x<32768;return x,at+2
  for i in range(count):
   at=pos+start+struct.unpack_from('<I',data,pos+header+4*i)[0]
   n,at=length(at)
   if utf8:n,at=length(at)
   value=data[at:at+n*(1 if utf8 else 2)].decode('utf-8' if utf8 else 'utf-16le')
   if value=='com.android.dialer':value='org.kyf37.dialerxx'
   elif value=='com.android.dialer.provider':value='org.kyf37.dialerxx.provider'
   elif value.startswith('.'):value='com.android.dialer'+value
   elif (smali/'com/android/dialer'/(value+'.smali')).is_file():value='com.android.dialer.'+value
   strings.append(value)
  offsets=[];payload=b''
  def enc_len(n):return bytes([n]) if n<128 else bytes([128|(n>>8),n&255])
  for value in strings:
   offsets.append(len(payload));raw=value.encode('utf-8' if utf8 else 'utf-16le')
   payload+=(enc_len(len(value))+enc_len(len(raw))+raw+b'\0') if utf8 else struct.pack('<H',len(raw)//2)+raw+b'\0\0'
  payload+=b'\0'*((-len(payload))%4)
  start=header+4*count;newSize=start+len(payload)
  chunk=struct.pack('<HHI5I',1,header,newSize,count,0,flags,start,0)+b''.join(struct.pack('<I',x) for x in offsets)+payload
  data=data[:pos]+chunk+data[pos+size:]
  return data[:4]+struct.pack('<I',len(data))+data[8:]
 raise RuntimeError('No manifest string pool')
with zipfile.ZipFile(r/'stock-system/priv-app/Dialer/Dialer.apk') as zin,zipfile.ZipFile(stage/'Dialer-unsigned.apk','w',zipfile.ZIP_DEFLATED) as zout:
 for info in zin.infolist():
  if info.filename.startswith('META-INF/') or info.filename.endswith('.dex'):continue
  data=zin.read(info.filename)
  if info.filename=='AndroidManifest.xml':
   data=patch_manifest(data)
   manifestCompat=runpy.run_path(str(Path(__file__).with_name('stock-manifest-compat.py')))
   data=manifestCompat['add_permissions'](data,['android.permission.RECORD_AUDIO','android.permission.CAPTURE_AUDIO_OUTPUT'],'org.kyf37.compat.CallMemoActivity')
  if info.filename=='resources.arsc' or (info.filename.startswith('res/') and info.filename.endswith('.xml')) or info.filename=='AndroidManifest.xml':
   data=compat['remap_binary'](data,ids)
  zout.writestr(info,data)
 zout.write(stage/'classes.dex','classes.dex')
 zout.write(r/'kyocera-compat.dex','classes2.dex')
 with zipfile.ZipFile(Path(__file__).resolve().parent.parent/'kyf37-rom/SystemUI-stock.apk') as stock:
  for name in ['k_i_co_btn_softkey_base','k_c_co_btn_softkey_left_up_normal','k_c_co_btn_softkey_left_down_normal','k_c_co_btn_softkey_center_normal','k_c_co_btn_softkey_right_up_normal','k_c_co_btn_softkey_right_down_normal']:
   zout.writestr('assets/kyf37-native-softkeys/'+name+'.png',stock.read('res/drawable-hdpi-v4/'+name+'.png'))
run('bash','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/sign-test-apk.sh',stage/'Dialer-unsigned.apk',stage/'Kyf37StockDialer.apk')
folder=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/stock-dialer-port');folder.mkdir(exist_ok=True)
shutil.copy2(stage/'Kyf37StockDialer.apk',folder/'Kyf37StockDialer.apk')
print('Stock phone test port assembled with separate package and provider authority')
