"""Prepare generated Sky Star art, add a third Appearance option. WSL Python."""
from pathlib import Path
import importlib.util, json, re, shutil, sys, zipfile

WS=Path(__file__).resolve().parent.parent
ROOT=Path('/home/pablo/kyf37-android10')
PACK=WS/'kyf37-rom/sky-star-icons'
def module(filename):
    spec=importlib.util.spec_from_file_location(filename,WS/'device-inspection'/filename)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=module('fix-android10-pastel-icons.py')
extra=module('fix-android10-pastel-settings-icons.py')
NAMES=base.NAMES+extra.NAMES

def prepare():
    from PIL import Image, ImageDraw
    atlas=Image.open(PACK/'atlas.png').convert('RGBA')
    assert atlas.getextrema()[3][0]==0,'Need genuine transparent artwork'
    alpha=atlas.getchannel('A')
    def cuts(vertical,count):
        size=atlas.width if vertical else atlas.height
        projection=[sum(alpha.crop((i,0,i+1,atlas.height) if vertical else (0,i,atlas.width,i+1)).getdata()) for i in range(size)]
        out=[0]
        for k in range(1,count):
            center=k*size/count
            lo,hi=round(center-size/count*.32),round(center+size/count*.32)
            out.append(min(range(lo,hi),key=lambda i:(projection[i],abs(i-center))))
        return out+[size]
    xs,ys=cuts(True,8),cuts(False,10)
    (PACK/'icons').mkdir(exist_ok=True)
    preview=Image.new('RGB',(8*192,10*216),'#dff4ff')
    draw=ImageDraw.Draw(preview)
    for i,name in enumerate(NAMES):
        x,y=i%8,i//8
        tile=atlas.crop((xs[x],ys[y],xs[x+1],ys[y+1]))
        assert tile.getbbox(),name
        tile=tile.crop(tile.getbbox());tile.thumbnail((164,164),Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',(192,192))
        canvas.paste(tile,((192-tile.width)//2,(192-tile.height)//2))
        canvas.save(PACK/'icons'/('sky_'+name+'.png'))
        preview.paste(canvas,(x*192,y*216),canvas)
        draw.text((x*192+10,y*216+194),name.replace('_',' '),fill='#163d70')
    preview.save(PACK/'preview.png')
    mapping={p:name for name,packages in base.GROUPS.items() for p in packages.split()}
    (PACK/'packages.properties').write_text(''.join(p+'='+n+'\n' for p,n in sorted(mapping.items())))
    (PACK/'packages.json').write_text(json.dumps(mapping,indent=2)+'\n')
    (PACK/'crop-grid.json').write_text(json.dumps({'x':xs,'y':ys,'order':NAMES},indent=2)+'\n')
    activities=re.findall(r'([\w.]+)/[\w.]+',(PACK/'launcher-activities.txt').read_text()) if (PACK/'launcher-activities.txt').exists() else []
    coverage={'icons':len(NAMES),'launcher_activities':len(activities),'unmapped_launchers':[p for p in activities if p not in mapping]}
    assert not coverage['unmapped_launchers'],coverage
    (PACK/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    with zipfile.ZipFile(PACK/'sky-star-icon-pack.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((PACK/'icons').glob('*.png')):z.write(p,'icons/'+p.name)
        for n in ('preview.png','packages.properties','packages.json','generation-prompt.txt','color-revision-prompt.txt','README.md','coverage.json'):
            if (PACK/n).exists():z.write(PACK/n,n)
    print('Prepared',len(NAMES),'Sky Star icons',xs,ys)

def apply():
    home=ROOT/'packages/apps/Kyf37Home'
    phone=ROOT/'packages/apps/Kyf37PhoneSettings'
    settings=ROOT/'packages/apps/Settings'
    assert len(list((PACK/'icons').glob('sky_*.png')))==80
    assets=home/'assets/sky-star';assets.mkdir(parents=True,exist_ok=True)
    for p in (PACK/'icons').glob('*.png'):shutil.copy2(p,assets/p.name)
    shutil.copy2(PACK/'packages.properties',assets/'packages.properties')
    for app in (phone,settings):
        out=app/'res/drawable-nodpi';out.mkdir(exist_ok=True)
        for p in (PACK/'icons').glob('*.png'):shutil.copy2(p,out/p.name)
    # Retain the existing package mapping and key, avoiding duplicated loader classes.
    p=WS/'device-inspection/Kyf37PastelIcons.java.txt';s=p.read_text()
    if 'String folder =' not in s:
        s=s.replace('String name = packages.getProperty(pkg, "generic");',
            'String name = packages.getProperty(pkg, "generic");\n        boolean sky = android.provider.Settings.Global.getInt(context.getContentResolver(),"kyf37_icon_theme",1)==2;\n        String folder = sky ? "sky-star/sky_" : "pastel-star/pastel_";\n        String cacheKey = folder + name;')
        s=s.replace('cache.get(name)','cache.get(cacheKey)').replace('cache.put(name,','cache.put(cacheKey,')
        s=s.replace('"pastel-star/pastel_" + name + ".png"','folder + name + ".png"')
    p.write_text(s);shutil.copy2(p,home/'src/org/kyf37/home/PastelIcons.java')
    p=WS/'device-inspection/Kyf37AppearanceSettings.java.txt';s=p.read_text()
    s=s.replace('{"Standard", "Pastel Star"}','{"Standard", "Pastel Star", "Sky Star"}')
    s=s.replace('Settings.Global.getInt(getContentResolver(),KEY,1)==0 ? 0 : 1','Math.max(0,Math.min(2,Settings.Global.getInt(getContentResolver(),KEY,1)))')
    s=s.replace('checked!=100 && checked!=101','checked<100 || checked>102')
    s=s.replace('KEY,checked==100?0:1','KEY,checked-100')
    s=s.replace('checked==100?"Standard icons":"Pastel Star icons"','new String[]{"Standard icons","Pastel Star icons","Sky Star icons"}[checked-100]')
    s=s.replace('in either theme','in every theme')
    p.write_text(s);shutil.copy2(p,phone/'src/org/kyf37/phonesettings/AppearanceSettings.java')
    for p in (phone/'src/org/kyf37/phonesettings/PhoneSettings.java',WS/'device-inspection/Kyf37PhoneSettings.java.txt'):
        s=p.read_text()
        if 'int[] skyIcons' not in s:
            m=re.search(r'    private final int\[\] pastelIcons = \{.*?\};',s,re.S)
            assert m,p
            s=s[:m.end()]+'\n'+m.group().replace('pastelIcons','skyIcons').replace('ic_pastel_','sky_')+s[m.end():]
        s=s.replace('setImageResource(pastelIcons[i])','setImageResource(Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==2 ? skyIcons[i] : pastelIcons[i])')
        s=s.replace('==0 ? "Standard" : "Pastel Star"','==0 ? "Standard" : (Settings.Global.getInt(getContentResolver(),"kyf37_icon_theme",1)==2 ? "Sky Star" : "Pastel Star")')
        p.write_text(s)
    p=WS/'device-inspection/Kyf37ThemeDrawable.java.txt';s=p.read_text()
    s=s.replace('private static boolean pastel=true;','private static int themeId=1;')
    s=s.replace('private Drawable standard, themed;','private Drawable standard, themed, sky;')
    s=s.replace('pastel=Settings.Global.getInt(c.getContentResolver(),KEY,1)!=0;','themeId=Settings.Global.getInt(c.getContentResolver(),KEY,1);')
    if 'String skyName=' not in s:
        s=s.replace('themed=r.getDrawable(a.getResourceId(1,0),theme);','''themed=r.getDrawable(a.getResourceId(1,0),theme);
            String skyName=r.getResourceEntryName(a.getResourceId(1,0)).replace("pastel_","sky_");
            int skyId=r.getIdentifier(skyName,"drawable","com.android.settings");
            sky=skyId==0?themed:r.getDrawable(skyId,theme);''')
    s=s.replace('Drawable d=pastel?themed:standard;','Drawable d=themeId==0?standard:(themeId==2?sky:themed);')
    s=s.replace('d.setColorFilter(pastel?null:filter)','d.setColorFilter(themeId==0?filter:null)')
    p.write_text(s);shutil.copy2(p,settings/'src/com/android/settings/widget/Kyf37ThemeDrawable.java')
    p=settings/'res/xml/top_level_settings.xml'
    p.write_text(p.read_text().replace('Standard or Pastel Star icons','Standard, Pastel Star or Sky Star icons'))
    print('Sky Star staged as theme 2; native and Pastel themes retained')
if __name__=='__main__':
    if '--prepare' in sys.argv:prepare()
    else:apply()
