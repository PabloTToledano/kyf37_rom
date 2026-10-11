"""Export a clean, publishable copy of the workspace (text sources + docs only) for the GitHub repository.
Usage (Windows):  python tools/export-repo.py [--dest \\wsl$\\Ubuntu\\home\\pablo\\kyf37_rom_stage] [--list-only]
Whitelist based: nothing is exported unless it matches a rule below, so firmware, images, backups, keys, APKs, logs and personal data
can never leak because somebody forgot a .gitignore line. Then run the secret scan (tools/scan-export.py) on the result."""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TEXT_EXT = {'.py', '.sh', '.ps1', '.md', '.txt', '.inc', '.java', '.c', '.cpp', '.h', '.bp', '.mk', '.rc', '.xml', '.json', '.patch', '.diff',
            '.conf', '.cfg', '.prop', '.html', '.css', '.kl', '.in', '.mak', '.cmake', '.yaml', '.yml', '.toml', '.ini', '.sha256', ''}
SKIP_DIRS = {'recovery-venv', 'stock-resource-venv', '__pycache__', 'scrcpy', 'node_modules', '.git', 'site', 'fontwork', 'phone-backup', 'archive',
             'radio-work', 'modem-investigation', 'tt9', 'librecamera', 'outer-animation', 'keypad-ui-validation', 'afphome', 'twrp-recovery-src', 'recovery-restart-capture'}
SECRET_NAME = re.compile(r'(\.pem|\.key|\.keystore|\.jks|\.p12|signing|owner-key|id_rsa)', re.I)
MAX_BYTES = 300_000          # general text file cap
JSON_MAX = 100_000
EXTRA_FILES = ['device-inspection/outer-v2/outerfont.bin', 'device-inspection/kyf37-tama/res/drawable-nodpi/ic_tama.png']
ROOT_FILES = ['README.md', 'LICENSE', 'NOTICE', '.gitignore', 'AGENTS.md', 'KYF37-PROJECT.md']
TOP = ['docs', 'device-inspection', 'tools', 'kyf37-twrp-device', 'kyf37-rom', 'kernel-port-research']

def wanted(rel):
    name = os.path.basename(rel)
    ext = os.path.splitext(name)[1].lower()
    parts = rel.replace('\\', '/').split('/')
    if SECRET_NAME.search(name) or re.search(r'tama' + r'web', rel, re.I): return False
    if rel.replace('\\', '/') in EXTRA_FILES: return True
    top = parts[0]
    if top == 'docs':
        return ext in ('.md', '.png') and os.path.getsize(rel) < 600_000
    if top == 'kyf37-rom':
        if len(parts) == 2:   # loose release notes / hashes / validation reports
            return (ext in ('.md', '.sha256') or name.endswith('-validation.json') or name.endswith('.sh')) and os.path.getsize(rel) < JSON_MAX
        return ext == '.md' and os.path.getsize(rel) < 60_000
    if top == 'kyf37-twrp-device':
        return ext in ('.xml', '.mk', '.md', '.sh', '.py', '.rc', '.fstab', '.txt', '.prop', '.json') and os.path.getsize(rel) < 100_000
    if ext not in TEXT_EXT: return False
    size = os.path.getsize(rel)
    if ext == '.json': return size < JSON_MAX and top != 'kernel-port-research'
    if ext in ('.txt', '') and size > 100_000: return False
    if name.endswith(('.log', '.log.txt')): return False
    return size < MAX_BYTES

def walk():
    for f in ROOT_FILES:
        if os.path.exists(f): yield f
    for top in TOP:
        for base, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and 'venv' not in d and 'tombstone' not in d and not d.startswith('.')]
            for fn in files:
                rel = os.path.join(base, fn).replace('\\', '/')
                try:
                    if wanted(rel): yield rel
                except OSError:
                    pass
    for f in EXTRA_FILES:
        if os.path.exists(f): yield f

files = sorted(set(walk()))
print(len(files), 'files,', round(sum(os.path.getsize(f) for f in files) / 1048576, 1), 'MB')
dest = None
if '--dest' in sys.argv: dest = sys.argv[sys.argv.index('--dest') + 1]
if '--list-only' in sys.argv or not dest:
    open('export-list.txt', 'w').write('\n'.join(files)); sys.exit(0)
REDACT = [(re.compile(r'(?<!\d)35\d{13}(?!\d)'), '<IMEI>'),
          (re.compile(r'DIGI' r'FIBRA-\w+'), '<home-ap>'),
          (re.compile(r'(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:])'), 'xx:xx:xx:xx:xx:xx')]
SCRUB = re.compile(r'tama' + r'web|auto' + r'sam|saman' + r'dev', re.I)   # third-party game: no references in the public repo
def redact(path):
    if os.path.splitext(path)[1].lower() not in TEXT_EXT or os.path.getsize(path) > 2_000_000: return
    try: text = open(path, encoding='utf-8', errors='surrogateescape').read()
    except OSError: return
    new = text
    for rx, rep in REDACT: new = rx.sub(rep, new)
    new = ''.join(l for l in new.splitlines(True) if not SCRUB.search(l))
    if new != text: open(path, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(new)
if os.path.exists(dest): shutil.rmtree(dest)
for f in files:
    t = os.path.join(dest, f)
    os.makedirs(os.path.dirname(t), exist_ok=True)
    shutil.copy2(f, t)
    redact(t)
print('exported to', dest)
