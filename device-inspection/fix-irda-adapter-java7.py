from pathlib import Path
p=Path('/home/pablo/kyf37-rom/irda-compat/src/jp/kyocera/kcfp/app/KCfpActivityManagerUtil.java')
s=p.read_text().replace('(d,w)->finish()','new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int w){finish();}}')
p.write_text(s)
