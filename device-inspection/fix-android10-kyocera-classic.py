"""Idempotent fourth icon theme and owner wallpaper, staged after older UI generators."""
from pathlib import Path
import re,shutil
WS=Path(__file__).resolve().parent.parent
ROOT=Path('/home/pablo/kyf37-android10');PACK=WS/'kyf37-rom/kyocera-classic'
home=ROOT/'packages/apps/Kyf37Home';phone=ROOT/'packages/apps/Kyf37PhoneSettings';settings=ROOT/'packages/apps/Settings'
def copy(src,dst):
 src,dst=Path(src),Path(dst)
 if not dst.exists() or dst.read_bytes()!=src.read_bytes():shutil.copyfile(src,dst)
assert len(list((PACK/'icons').glob('classic_*.png')))==80
for target in [home/'assets/kyocera-classic',phone/'res/drawable-nodpi',settings/'res/drawable-nodpi']:
 target.mkdir(parents=True,exist_ok=True)
 for p in (PACK/'icons').glob('*.png'):copy(p,target/p.name)
def edit(p,fn):
 s=p.read_text();n=fn(s)
 if s!=n:p.write_text(n)
def loader(s):
 if '// Current Kyocera port mappings' not in s:
  overrides={'com.kyocera.calculator2':'calculator','jp.kyocera.charactercheck':'keypad','jp.kyocera.datafolder':'files','org.kyf37.dialerxx':'phone','org.kyf37.dialer':'phone','org.kyf37.messages':'messages','org.kyf37.contacts':'contacts','com.android.camera2':'camera'}
  java='\n                // Current Kyocera port mappings\n'+''.join('                packages.setProperty("'+k+'","'+v+'");\n' for k,v in overrides.items())
  s=s.replace('packages.load(in);','packages.load(in);'+java)
 s=s.replace('boolean sky = android.provider.Settings.Global.getInt(context.getContentResolver(),"kyf37_icon_theme",1)==2;', 'int themeId = android.provider.Settings.Global.getInt(context.getContentResolver(),"kyf37_icon_theme",1);')
 s=s.replace('String folder = sky ? "sky-star/sky_" : "pastel-star/pastel_";', 'String folder = themeId==3 ? "kyocera-classic/classic_" : (themeId==2 ? "sky-star/sky_" : "pastel-star/pastel_");')
 if 'packages.setProperty("com.android.camera2","camera");' not in s:
  s=s.replace('packages.load(in);','packages.load(in);\n                packages.setProperty("com.android.camera2","camera");')
 return s
edit(WS/'device-inspection/Kyf37PastelIcons.java.txt',loader)
copy(WS/'device-inspection/Kyf37PastelIcons.java.txt',home/'src/org/kyf37/home/PastelIcons.java')
def appearance(s):
 s=s.replace('"Pastel Star", "Sky Star"}', '"Pastel Star", "Sky Star", "Kyocera Classic"}')
 s=s.replace('Math.min(2, Settings.Global.getInt(getContentResolver(), ICON_KEY, 1))','Math.min(3, Settings.Global.getInt(getContentResolver(), ICON_KEY, 1))')
 s=s.replace('checked > 102','checked > 103').replace('"Sky Star icons"}', '"Sky Star icons", "Kyocera Classic icons"}')
 return s
edit(WS/'device-inspection/Kyf37AppearanceSettings.java.txt',appearance)
copy(WS/'device-inspection/Kyf37AppearanceSettings.java.txt',phone/'src/org/kyf37/phonesettings/AppearanceSettings.java')
def rows(s):
 if 'int[] classicIcons' not in s:
  m=re.search(r'    private final int\[\] skyIcons = \{.*?\};',s,re.S);assert m
  s=s[:m.end()]+'\n'+m.group().replace('skyIcons','classicIcons').replace('sky_','classic_')+s[m.end():]
 s=re.sub(r'setImageResource\(Settings.Global.getInt\(getContentResolver\(\),"kyf37_icon_theme",1\).*?;', 'setImageResource(Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==3 ? classicIcons[i] : (Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==2 ? skyIcons[i] : pastelIcons[i]));',s)
 s=re.sub(r'case 14: return Settings.Global.getInt\(getContentResolver\(\),"kyf37_icon_theme",1\).*?;', 'case 14: return new String[]{"Standard","Pastel Star","Sky Star","Kyocera Classic"}[Math.max(0,Math.min(3,Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)))];',s)
 return s
for p in [WS/'device-inspection/Kyf37PhoneSettings.java.txt',phone/'src/org/kyf37/phonesettings/PhoneSettings.java']:edit(p,rows)
def drawable(s):
 s=s.replace('private Drawable standard, themed, sky;', 'private Drawable standard, themed, sky, classic;')
 if 'String classicName=' not in s:
  anchor='            sky=skyId==0?themed:r.getDrawable(skyId,theme);';assert anchor in s
  s=s.replace(anchor,anchor+'\n            String classicName=skyName.replace("sky_","classic_");\n            int classicId=r.getIdentifier(classicName,"drawable","com.android.settings");\n            classic=classicId==0?standard:r.getDrawable(classicId,theme);')
 return s.replace('Drawable d=themeId==0?standard:(themeId==2?sky:themed);','Drawable d=themeId==0?standard:(themeId==3?classic:(themeId==2?sky:themed));')
edit(WS/'device-inspection/Kyf37ThemeDrawable.java.txt',drawable)
copy(WS/'device-inspection/Kyf37ThemeDrawable.java.txt',settings/'src/com/android/settings/widget/Kyf37ThemeDrawable.java')
edit(settings/'res/xml/top_level_settings.xml',lambda s:s.replace('Standard, Pastel Star or Sky Star icons','Standard, Pastel Star, Sky Star or Kyocera Classic icons'))
# Folder headings must use the same contrast sampler as app labels.
for p in [WS/'device-inspection/Kyf37Home.java.txt',home/'src/org/kyf37/home/Home.java']:
 def home_fixes(s):
  if 'wallpaperContrast.apply(folderTitle)' not in s:
   s=s.replace('wallpaperContrast.apply(dateText);','wallpaperContrast.apply(dateText);\n              if(folderTitle!=null)wallpaperContrast.apply(folderTitle);')
  s=s.replace('new Intent(android.provider.MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA));','new Intent(android.provider.MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA).setPackage(installed(pm,"com.android.camera2") ? "com.android.camera2" : (installed(pm,"jp.kyocera.camera") ? "jp.kyocera.camera" : null)));')
  return s
 edit(p,home_fixes)
for p in [WS/'device-inspection/wallpaper/owner-wallpaper.png',home/'assets/owner-wallpaper.png',ROOT/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/drawable-nodpi/default_wallpaper.png',ROOT/'device/kyocera/kyf37/overlay/frameworks/base/core/res/res/drawable-hdpi/default_wallpaper.png',WS/'kyf37-rom/default_wallpaper.png']:
 p.parent.mkdir(parents=True,exist_ok=True);copy(PACK/'wallpaper.png',p)
# Lineage's common overlay is linked after the device overlay on this tree.
# Replace its existing handset variants too; both are tracked upstream assets.
for qualifier in ['drawable-nodpi','drawable-hdpi']:
 p=ROOT/'vendor/lineage/overlay/common/frameworks/base/core/res/res'/qualifier/'default_wallpaper.png'
 assert p.exists(),p
 if p.read_bytes()!=(PACK/'wallpaper.png').read_bytes():copy(PACK/'wallpaper.png',p)
print('Kyocera Classic theme 3, wallpaper default and folder-title contrast staged')
