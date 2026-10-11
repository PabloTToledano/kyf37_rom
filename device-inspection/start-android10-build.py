"""Start a resumable detached build whose lifetime does not depend on the tool PTY."""
from pathlib import Path
import subprocess, json, shutil
base = Path('/home/pablo')
if subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('A build is already running; refusing to start another.')
log = base/'kyf37-android10-build.log'
if log.exists():
    shutil.copy2(log, base/'kyf37-android10-build-previous.log')
with log.open('wb') as stream:
    process = subprocess.Popen(['bash','/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-kyf37-android10.sh'],
        stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
state={'pid':process.pid,'log':str(log),'runtime_verified':False}
(base/'kyf37-android10-build-process.json').write_text(json.dumps(state)+'\n')
print(json.dumps(state))
