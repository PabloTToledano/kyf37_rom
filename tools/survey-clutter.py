"""Survey kyf37-rom top-level entries: size, mtime and how many repo scripts mention each name. Read-only.
Usage: python tools/survey-clutter.py > survey.txt"""
import os, re, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIRS = ['device-inspection', 'tools']
EXT = ('.py', '.sh', '.ps1', '.txt', '.mk', '.c', '.java', '.inc', '.json')
corpus = []
for d in SCRIPT_DIRS:
    for base, dirs, files in os.walk(os.path.join(ROOT, d)):
        dirs[:] = [x for x in dirs if x not in ('stock-resource-venv', 'node_modules', '__pycache__', 'scrcpy')]
        for f in files:
            if f.endswith(('.py', '.sh', '.ps1')):
                try:
                    corpus.append(open(os.path.join(base, f), encoding='utf-8', errors='ignore').read())
                except OSError:
                    pass
blob = '\n'.join(corpus)

def size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    t = 0
    for b, _, fs in os.walk(p):
        for f in fs:
            try: t += os.path.getsize(os.path.join(b, f))
            except OSError: pass
    return t

target = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'kyf37-rom')
rows = []
for name in sorted(os.listdir(target)):
    p = os.path.join(target, name)
    refs = blob.count(name)
    rows.append((name, size(p), time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p))), refs, 'D' if os.path.isdir(p) else 'F'))
for r in rows:
    print('%-70s %10.1fMB %s refs=%-3d %s' % (r[0][:70], r[1] / 1048576, r[2], r[3], r[4]))
print('TOTAL %.1f MB' % (sum(r[1] for r in rows) / 1048576))
