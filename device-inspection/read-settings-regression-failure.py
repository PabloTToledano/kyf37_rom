from pathlib import Path
s=Path('/home/pablo/kyf37-settings-regression.log').read_text(errors='replace')
a=s.find('There were');print(s[a:a+4300])
