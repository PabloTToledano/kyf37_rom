from pathlib import Path
import re
r=Path('/home/pablo/kyf37-rom/stock-dialer-port/backend-reference/Telecom')
for p in r.rglob('*.smali'):
 text=p.read_text()
 if 'Landroid/media/MediaPlayer;->setAudioStreamType' not in text:continue
 if 'PhoneMemoPlayActivity' in p.name or 'TelecomUiService' in p.name:continue
 print(p.relative_to(r))
 for b in re.findall(r'\.method.*?\.end method',text,re.S):
  if 'setAudioStreamType' in b or 'setParameters' in b or 'setAttribute' in b:print(b[:10000])
