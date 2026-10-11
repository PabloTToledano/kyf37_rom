from pathlib import Path
r=Path('/home/pablo/kyf37-rom')
for p in (r/'stock-system').rglob('*.apk'):
 if any(x in p.name.lower() for x in ['felica','nfc','osaifu']):print(p)
p=r/'vendor-framework-smali/jp/kyocera/kcfp/app/KCfpActivityManagerUtil.smali'
s=p.read_text();print(s[:6000])
