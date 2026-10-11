"""Release gate for complete native softkey dex and exact owner stock artwork."""
from pathlib import Path
import zipfile,hashlib,json,argparse
parser=argparse.ArgumentParser();parser.add_argument('--tree',type=Path,default=Path('/home/pablo/kyf37-android10'));args=parser.parse_args()
here=Path(__file__).resolve().parent
names=['k_i_co_btn_softkey_base','k_c_co_btn_softkey_left_up_normal','k_c_co_btn_softkey_left_down_normal','k_c_co_btn_softkey_center_normal','k_c_co_btn_softkey_right_up_normal','k_c_co_btn_softkey_right_down_normal']
with zipfile.ZipFile(here.parent/'kyf37-rom/SystemUI-stock.apk') as stock:
 expected={n:hashlib.sha256(stock.read('res/drawable-hdpi-v4/'+n+'.png')).hexdigest() for n in names}
checked=[]
for module in ['KyoceraCamera','MemoPad','MemoPadProvider','Reader','kc_soundrecorder','kc_soundrecorder_manager']:
 apk=args.tree/'out/target/product/kyf37/system/app'/module/(module+'.apk')
 with zipfile.ZipFile(apk) as z:
  dex=z.read('classes2.dex')
  for value in [b'Ljp/kyocera/kcfp/util/Kyf37SoftkeyBridge;',b'Ljp/kyocera/kcfp/util/KCfpSoftkeyGuide$Softkeys;',b'resourcesPackage',b'mergeFrom']:
   assert value in dex, (module,'Native softkey helper missing',value)
  for name,want in expected.items():assert hashlib.sha256(z.read('assets/kyf37-native-softkeys/'+name+'.png')).hexdigest()==want,(module,name)
 checked.append(module)
print(json.dumps({'native_softkey_modules_verified':checked,'original_artwork_verified':True,'hardware_verified':False},indent=2))
