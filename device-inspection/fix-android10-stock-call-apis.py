"""Stage concrete public-API migrations, preserving still-unported OEM operations."""
from pathlib import Path
import subprocess,shutil,re,json
here=Path(__file__).resolve().parent;r=Path('/home/pablo/kyf37-rom');stage=r/'stock-dialer-port';java=Path('/home/pablo/kyf37-host-tools/jdk8/bin');src=stage/'call-compat-src/org/kyf37/compat';src.mkdir(parents=True,exist_ok=True)
for filename in ['Kyf37CallCompat.java','CallMemoActivity.java']:
 (src/filename).write_text((here/'kyocera-port'/filename).read_text(encoding='utf-8-sig'))
classes=stage/'call-compat-classes';classes.mkdir(exist_ok=True)
def run(*args):subprocess.run([str(x) for x in args],check=True)
run(java/'javac','-source','7','-target','7','-bootclasspath',here.parent/'kyf37-rom/android-7-sdk-classes.jar','-d',classes,src/'Kyf37CallCompat.java',src/'CallMemoActivity.java')
run(java/'java','-jar','/home/pablo/kyf37-lineage/prebuilts/sdk/tools/lib/dx.jar','--dex','--output='+str(stage/'call-compat.dex'),classes)
helper=stage/'call-compat-smali';run(java/'java','-jar',r/'tools/baksmali.jar','disassemble',stage/'call-compat.dex','-o',helper)
smali=stage/'smali';shutil.copytree(helper,smali,dirs_exist_ok=True)
owner='Lorg/kyf37/compat/Kyf37CallCompat;'
mapping={
 'android/telecom/Call': {'getSubState','getRejectType','destroy','deflectCall','startTalkingMemo','stopTalkingMemo','setCallFowarding','answerUnholding'},
 'android/telecom/Call$Details':{'getCallSubstate','getCodecMode'},
 'android/telecom/TelecomManager':{'hasMultipleCallCapableAccounts','setReceiveMute','setIncallUiActiveState','selectSaveAutoTalkMemo'},
 'android/telecom/Phone':{'setHeardEffect','switchToOtherActiveSub'},
 'android/telecom/PhoneAccount':{'createIconDrawable'},
 'android/telecom/InCallService$VideoCall':{'setVideoCallListener'}
}
count=0
for p in smali.rglob('*.smali'):
 if 'org/kyf37/compat/' in str(p):continue
 text=p.read_text()
 def migrate(m):
  global count
  cls,name,desc=m['class'],m['name'],m['desc']
  if name not in mapping.get(cls,set()):return m[0]
  count+=1;sig='(L'+cls+';'+desc[1:]
  if cls=='android/telecom/Phone':sig=sig.replace('(Landroid/telecom/Phone;','(Ljava/lang/Object;')
  if name=='setVideoCallListener':sig=sig.replace('Landroid/telecom/InCallService$VideoCall$Listener;','Ljava/lang/Object;')
  return 'invoke-static'+(m['range'] or '')+' '+m['regs']+', '+owner+'->'+name+sig
 text=re.sub(r'invoke-virtual(?P<range>/range)? (?P<regs>\{[^}]*\}), L(?P<class>android/telecom/[^;]+);->(?P<name>\w+)(?P<desc>\([^\n\s]+)',migrate,text)
 text=text.replace('Landroid/telecom/VideoProfile$VideoState;->is','Landroid/telecom/VideoProfile;->is')
 # OEM logging flag disappeared; use the actual current build debug flag.
 text=text.replace('Lcom/android/internal/telephony/PhoneConstants;->DEBUG:Z', 'Landroid/os/Build;->IS_DEBUGGABLE:Z')
 # The full original Window ABI now delegates to the restored app-local bar.
 text=re.sub(r'invoke-virtual(?P<range>/range)? (?P<regs>\{[^}]*\}), Landroid/view/Window;->(?P<name>getSoftkeyGuide|getCurrentSoftkeys|getAttributSoftkeys|setSoftkeys)(?P<desc>\([^\n\s]+)',lambda m:'invoke-static'+(m['range'] or '')+' '+m['regs']+', Ljp/kyocera/kcfp/util/Kyf37SoftkeyBridge;->'+m['name']+'(Landroid/view/Window;'+m['desc'][1:],text)
 if p.name=='DialerApplication.smali' and 'Kyf37CallCompat;->attach' not in text:
  # Add after the register count so .locals/.registers semantics are unchanged.
  text=re.sub(r'(\.method public onCreate\(\)V\s*\n\s*\.(?:registers|locals) \d+)',lambda m:m[1]+'\n    invoke-static {p0}, '+owner+'->attach(Landroid/content/Context;)V',text)
 p.write_text(text)
(stage/'call-api-migrations.json').write_text(json.dumps({'rewritten_invocations':count,'mappings':{k:sorted(v) for k,v in mapping.items()}},indent=2))
print('Concrete call API migrations:',count)
