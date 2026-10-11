"""Prepare local audio and adaptive outer-screen video; image conversion uses Windows Python."""
from pathlib import Path
import subprocess,os,sys
w=Path(__file__).resolve().parent.parent;p=w/'third-party/bad-apple';a=p/'assets';a.mkdir(exist_ok=True)
source=p/'BadApple.mp4'
def linux(path):
 s=str(path.resolve()).replace('\\','/');return '/mnt/'+s[0].lower()+s[2:] if os.name=='nt' else s
cmd=['ffmpeg','-y','-v','error','-i',linux(source),'-vn','-ac','1','-ar','22050','-c:a','aac','-b:a','48k',linux(a/'badapple.m4a')]
if os.name=='nt':cmd=['wsl','-d','Ubuntu','--']+cmd
subprocess.run(cmd,check=True)
wide=w/'device-inspection/prepare-bad-apple-wide.py'
if os.name=='nt':subprocess.run([sys.executable,str(wide)],check=True)
else:subprocess.run(['cmd.exe','/c','python',str(wide).replace('/mnt/c/','C:/')],check=True)
(p/'README.md').write_text('Bad Apple!! video and song (Alstroemeria Records / nomico; Touhou fan animation). Downloaded from the public rkk-2s/bad-apple repository for owner-requested personal device playback. Media copyrights remain with their respective authors; repository code licensing does not grant a media redistribution license. Do not publish these media assets as project-owned artwork. Conversion: device-inspection/prepare-bad-apple.py; provenance and source SHA-256 in provenance.json. Adaptive wide framing: prepare-bad-apple-wide.py using installed Windows Pillow/NumPy and WSL ffmpeg.\n')
