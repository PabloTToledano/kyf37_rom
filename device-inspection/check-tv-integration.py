"""Static checks for the One Seg TV integration (run in WSL from anywhere). No build, no phone."""
import re, glob, collections, os
os.chdir('/home/pablo/kyf37-android10')
txt = open('device/kyocera/kyf37/tv-oem.mk').read().replace('\\\n', ' ')
pairs = re.findall(r'(device/kyocera/kyf37/\S+):(system/\S+)', txt)
print('copy entries:', len(pairs))
print('missing sources:', [s for s, d in pairs if not os.path.exists(s)])
dests = collections.Counter()
for f in glob.glob('device/kyocera/kyf37/*.mk') + glob.glob('vendor/kyocera/kyf37/*.mk'):
    for d in re.findall(r':(system/[^\s\\]+)', open(f).read()):
        dests[d] += 1
print('destinations defined more than once:', sorted({d for s, d in pairs if dests[d] > 1}))
bad = []
for s, d in pairs:
    if d.startswith('system/lib/') or d == 'system/bin/dtvserver':
        h = open(s, 'rb').read(20)
        if h[:4] != b'\x7fELF' or h[4] != 1 or int.from_bytes(h[18:20], 'little') != 40:
            bad.append(s)
print('not 32-bit ARM ELF:', bad)
mode = oct(os.stat('device/kyocera/kyf37/tv/system/bin/dtvserver').st_mode & 0o777)
print('dtvserver source mode:', mode)
