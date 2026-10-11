"""Let the ported native keypad apps receive their own F1-F4 actions."""
from pathlib import Path
import subprocess,re,zipfile
root=Path('/home/pablo/kyf37-android10');policy=root/'frameworks/base/services/core/java/com/android/server/policy'
aapt=root/'out/host/linux-x86/bin/aapt2'
packages={'jp.kyocera.afphome','org.kyf37.dialerxx'}
for apk in list((root/'packages/apps/Kyf37StockApps').glob('*.apk'))+list((root/'packages/apps/Kyf37RemainingStockApps').glob('*.apk')):
 if apk.parent.name=='Kyf37RemainingStockApps':
  with zipfile.ZipFile(apk) as z:
   appDex=z.read('classes.dex') if 'classes.dex' in z.namelist() else b''
  if b'Kyf37SoftkeyBridge' not in appDex and b'KCfpSoftkeyGuide' not in appDex:continue
 s=subprocess.check_output([str(aapt),'dump','badging',str(apk)],text=True)
 packages.add(re.search(r"package: name='([^']+)'",s)[1])
p=policy/'PhoneWindowManager.java';s=p.read_text();original=s;anchor='    private long interceptKeyBeforeDispatchingInner('
helper='''    private boolean isKyf37NativeSoftkeyApp(String name) {
        if (name == null) return false;
        switch (name) {
'''+''.join('            case "'+n+'":\n' for n in sorted(packages))+'''                return true;
            default: return false;
        }
    }

'''
s=re.sub(r'    private boolean isKyf37NativeSoftkeyApp\(String name\).*?\n    }\n\n','',s,flags=re.S)
s=s.replace(anchor,helper+anchor,1).replace('"jp.kyocera.afphome".equals(win.getOwningPackage())','isKyf37NativeSoftkeyApp(win.getOwningPackage())')
if s!=original:p.write_text(s)
p=policy/'Kyf37Navigation.java';s=p.read_text();original=s;anchor='        final int code = event.getKeyCode();'
if 'Native app labels own their key actions' not in s:
 s=s.replace(anchor,'''        // Native app labels own their key actions; do not replace F2/F3/F4.
        if (nativeKeys) {
            if (enabled) handler.post(new Runnable() { public void run() { reset(); } });
            return false;
        }
'''+anchor,1)
if s!=original:p.write_text(s)
print('Native softkey key dispatch:',', '.join(sorted(packages)))
