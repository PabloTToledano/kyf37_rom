"""Launch one isolated build continuation without shell quoting dependencies."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
log = root / 'logs/port-build.log'
with log.open('ab') as handle:
    child = subprocess.Popen(['bash', str(root / 'continue-318.sh'), '32575'],
                             stdin=subprocess.DEVNULL, stdout=handle,
                             stderr=subprocess.STDOUT, start_new_session=True)
(root / 'logs/pipeline.pid').write_text(str(child.pid) + '\n')
print('Started isolated pipeline PID', child.pid, 'log', log)
