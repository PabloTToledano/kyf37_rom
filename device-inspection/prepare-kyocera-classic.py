"""Prepare Kyocera Classic from original stock PNG artwork; Windows Python/Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import importlib.util, zipfile, io, json, hashlib
WS=Path(__file__).resolve().parent.parent
PACK=WS/'kyf37-rom/kyocera-classic'
STOCK=Path('//wsl.localhost/Ubuntu/home/pablo/kyf37-rom/stock-system')
def module(n):
 s=importlib.util.spec_from_file_location(n,WS/'device-inspection'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('fix-android10-pastel-icons.py');extra=module('fix-android10-pastel-settings-icons.py')
names=base.NAMES+extra.NAMES
menu=zipfile.ZipFile(STOCK/'priv-app/AfpHome/AfpHome.apk')
menu_map={'phone':'phone','contacts':'profile','camera':'camera','settings':'settings','phone_settings':'settings','files':'datafolder','gallery':'datafolder','browser':'browser','home':'tool','generic':'appli','security':'safety','privacy':'safety','accessibility':'safety','store':'appli','support':'tool','system':'settings'}
apk_map={'messages':'Mms','email':'Email','clock':'DeskClock','calendar':'Calendar','calculator':'Calculator','music':'Music','recorder':'kc_soundrecorder','memo':'MemoPad','flashlight':'MobileLight','qr':'Reader','infrared':'IrDA','keyboard':'iWnnIME','keypad':'Charactercheck','tv':'FsDtvApp','downloads':'DownloadProviderUi','bluetooth':'Bluetooth','backup':'BackupRestoreConfirmation','charactercheck':'Charactercheck'}
apks=list(STOCK.glob('*/*/*.apk'))
fw=zipfile.ZipFile(STOCK/'framework/framework-res.apk')
fw_map={'messages':'ic_menu_send','music':'ic_menu_music','wifi':'k_c_sb_ic_status_wifi_4','battery':'k_c_sb_ic_battery','display':'ic_menu_view','sound':'ic_lock_ringer_on_alpha','airplane':'ic_lock_airplane_mode_alpha','vibration':'ic_lock_silent_mode_vibrate','maps':'ic_menu_mapmode','compass':'ic_menu_compass','language':'ic_menu_set_as','notifications':'ic_menu_info_details','rotation':'ic_menu_always_landscape_portrait','video':'ic_media_play','downloads':'ic_menu_save','backup':'ic_menu_archive','mobile_data':'ic_menu_upload','hotspot':'ic_media_route_on_holo_light','usb':'ic_menu_attachment','terminal':'ic_menu_manage','update':'ic_menu_rotate','printer':'ic_menu_print','infrared':'ic_menu_share','sim':'ic_menu_account_list','keyboard':'ic_menu_edit','email':'ic_menu_send','store':'ic_menu_shopping','microg':'ic_menu_manage','tv':'ic_media_video_poster','equalizer':'ic_menu_sort_by_size','storage':'ic_menu_archive'}
sources={};(PACK/'icons').mkdir(parents=True,exist_ok=True)
for i,name in enumerate(names):
 raw=None
 if name in apk_map:
  candidates=[p for p in apks if p.parent.name.lower()==apk_map[name].lower()]
  for p in candidates:
   z=zipfile.ZipFile(p); entries=[n for n in z.namelist() if n.endswith('.png') and ('ic_launcher' in n or 'icon_app' in n or 'app_icon' in n)]
   entries.sort(key=lambda n:('launcher' not in n,'xxxhdpi' not in n,'xxhdpi' not in n,'xhdpi' not in n,'hdpi' not in n,len(n)))
   for n in entries:
    try:
     im=Image.open(io.BytesIO(z.read(n))).convert('RGBA')
     if min(im.size)<32:continue
     raw=im;sources[name]={'apk':str(p.relative_to(STOCK)),'entry':n};break
    except Exception:pass
   if raw is not None:break
 if raw is None and name in fw_map:
  entries=[n for n in fw.namelist() if n.endswith('/'+fw_map[name]+'.png')]
  if entries:
   entries.sort(key=lambda n:('xhdpi' not in n,'hdpi' not in n));n=entries[0]
   glyph=Image.open(io.BytesIO(fw.read(n))).convert('RGBA'); raw=Image.new('RGBA',glyph.size,'#356caa');raw.putalpha(glyph.getchannel('A'))
   sources[name]={'apk':'framework/framework-res.apk','entry':n}
 if raw is None:
  key=menu_map.get(name,'tool' if name in ['storage','usb','printer','hotspot','equalizer','battery'] else 'appli')
  n='res/drawable-hdpi-v4/k_c_co_mainmenu_'+key+'.png';raw=Image.open(io.BytesIO(menu.read(n))).convert('RGBA');sources[name]={'apk':'priv-app/AfpHome/AfpHome.apk','entry':n,'fallback':name not in menu_map}
 # Original geometry/colour retained inside a consistent sky-toned rounded tile.
 raw=raw.crop(raw.getbbox());raw.thumbnail((126,126),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(192,192));d=ImageDraw.Draw(out)
 d.rounded_rectangle((11,15,181,185),radius=38,fill=(35,78,113,30))
 d.rounded_rectangle((10,9,180,179),radius=38,fill='#f7fcff',outline='#8fc8ec',width=3)
 out.alpha_composite(raw,((192-raw.width)//2,(184-raw.height)//2))
 d=ImageDraw.Draw(out);d.ellipse((146,143,166,163),fill='#ffdc56',outline='#fff4bf',width=2)
 out.save(PACK/'icons'/('classic_'+name+'.png'))
preview=Image.new('RGB',(8*160,10*184),'#dff3ff');d=ImageDraw.Draw(preview)
for i,name in enumerate(names):
 im=Image.open(PACK/'icons'/('classic_'+name+'.png'));im.thumbnail((148,148),Image.Resampling.LANCZOS);x=i%8*160;y=i//8*184;preview.paste(im,(x+6,y),im);d.text((x+8,y+151),name.replace('_',' '),fill='#234d6d')
preview.save(PACK/'preview.png')
ImageOps.fit(Image.open(PACK/'wallpaper-original.png').convert('RGB'),(480,854),method=Image.Resampling.LANCZOS).save(PACK/'wallpaper.png')
(PACK/'artwork-sources.json').write_text(json.dumps(sources,indent=2))
(PACK/'provenance.txt').write_text('Derived from owner stock system APK PNG artwork. Kyocera Classic uses preserved original glyphs on custom sky/white rounded tiles. OEM art remains proprietary; personal ROM use. Unmatched categories use stock tool/app glyphs; not claimed individually redrawn. Wallpaper: owner attachment.\n')
print('Prepared',len(names),'icons;',sum('fallback' not in v or not v['fallback'] for v in sources.values()),'direct category sources')
