from pathlib import Path
p=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/v8-camera-test-last-kmsg.txt')
s=p.read_text(errors='replace');lines=s.splitlines()
for i,line in enumerate(lines):
 if 'kernel BUG' in line or 'Internal error:' in line:print('\n'.join(lines[max(0,i-3):i+7]))
