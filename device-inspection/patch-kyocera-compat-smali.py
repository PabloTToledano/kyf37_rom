"""Neutralise calls to Kyocera-only framework methods inside the compat smali, then reassemble kyocera-compat.dex. WSL.

Method presence is checked against Android 10's own framework classes (javap on framework classes.jar, hidden APIs included).
A missing void method call is deleted; a missing method with a result becomes a zero constant.
"""
import re, subprocess, shutil, json, zipfile
from pathlib import Path
r = Path('/home/pablo/kyf37-rom'); src = r / 'vendor-framework-smali'
stage = r / 'kyocera-compat-stage'
java = Path('/home/pablo/kyf37-host-tools/jdk8/bin')
fw = Path('/home/pablo/kyf37-android10/out/target/common/obj/JAVA_LIBRARIES/framework_intermediates/classes.jar')
extra = [Path('/home/pablo/kyf37-android10/out/target/common/obj/JAVA_LIBRARIES/core-oj_intermediates/classes.jar'),
         Path('/home/pablo/kyf37-android10/out/target/common/obj/JAVA_LIBRARIES/core-libart_intermediates/classes.jar')]
assert fw.is_file(), fw

shutil.rmtree(stage, ignore_errors=True)
for rel in ['jp/kyocera/kcfp', 'jp/kyocera/kerr', 'jp/kyocera/android', 'jp/kyocera/sublcd', 'jp/kyocera/internal', 'jp/kyocera/net']:
    if (src / rel).is_dir(): shutil.copytree(src / rel, stage / rel)

inv = re.compile(r'^(\s*)invoke-(\w+)(?:/range)? \{[^}]*\}, (L(?:android|com/android|java|javax|dalvik)/[^;]+);->([^(]+)(\([^)]*\)\S+)')
files = list(stage.rglob('*.smali'))
needed = {}
for f in files:
    for line in f.read_text().splitlines():
        m = inv.match(line)
        if m:
            needed.setdefault(m.group(3)[1:].replace('/', '.'), set()).add((m.group(4), m.group(5)))

cp = ':'.join(str(p) for p in [fw] + [e for e in extra if e.is_file()])
present = {}
def sig_of(smali_sig):
    return smali_sig  # javap -s prints the same JVM descriptors
for cls, methods in needed.items():
    p = subprocess.run([str(java / 'javap'), '-cp', cp, '-p', '-s', cls], capture_output=True, text=True)
    text = p.stdout
    have = set()
    if p.returncode == 0:
        lines = text.splitlines()
        for i, l in enumerate(lines):
            m = re.search(r'descriptor: (\(.*)', l)
            if m and i > 0:
                name = re.search(r'(\w+|<init>)\(', lines[i - 1])
                if name: have.add((name.group(1), m.group(1).strip()))
        # inherited methods: also search superclass chain/interfaces by name only
        sup = re.findall(r'(?:extends|implements) ([\w.$, ]+)', text.splitlines()[1] if len(text.splitlines()) > 1 else '')
    present[cls] = (have, p.returncode == 0, text)

missing = {}
for cls, methods in needed.items():
    have, ok, text = present[cls]
    if not ok:  # class not found at all
        missing[cls] = set(methods)
        continue
    for name, desc in methods:
        if name == '<init>' or (name, desc) in have: continue
        # inherited? check the superclass chain via javap of parents
        found = False
        queue = re.findall(r'(?:extends|implements) ([\w.$, ]+)', text)
        parents = [x.strip() for q in queue for x in q.split(',')]
        seen = set()
        while parents and not found:
            par = parents.pop()
            if par in seen: continue
            seen.add(par)
            p = subprocess.run([str(java / 'javap'), '-cp', cp, '-p', '-s', par], capture_output=True, text=True)
            if p.returncode != 0: continue
            lines = p.stdout.splitlines()
            for i, l in enumerate(lines):
                m = re.search(r'descriptor: (.*)', l)
                if m and i > 0 and re.search(r'\b' + re.escape(name) + r'\(', lines[i - 1]) and m.group(1).strip() == desc:
                    found = True; break
            for q in re.findall(r'(?:extends|implements) ([\w.$, ]+)', p.stdout):
                parents += [x.strip() for x in q.split(',')]
        if not found: missing.setdefault(cls, set()).add((name, desc))

for c in list(missing):
    if c.startswith('java.') or c in ('android.os.Bundle',): del missing[c]
report = {c: sorted(f'{n}{d}' for n, d in ms) for c, ms in missing.items()}
(r / 'kyocera-compat-missing.json').write_text(json.dumps(report, indent=1))
print(sum(len(v) for v in report.values()), 'missing android method refs in', len(report), 'classes')

patched = 0
for f in files:
    lines = f.read_text().split('\n'); out = []; i = 0; changed = False
    while i < len(lines):
        line = lines[i]; m = inv.match(line)
        if m:
            cls = m.group(3)[1:].replace('/', '.'); key = (m.group(4), m.group(5))
            if cls in missing and key in missing[cls]:
                ret = m.group(5).split(')')[1]
                out.append(m.group(1) + '# KYF37: Kyocera-only framework method removed: ' + line.strip())
                out.append(m.group(1) + 'nop')
                # move-result may be separated from the invoke by .line/label directives
                k = i + 1
                while k < len(lines) and re.match(r'\s*(\.line|\.local|\.prologue|.catch|:\S+|$)', lines[k]): k += 1
                mr = re.match(r'(\s*)move-result(-wide|-object)?\s+(\S+)', lines[k]) if k < len(lines) else None
                if mr:
                    reg = mr.group(3)
                    lines[k] = mr.group(1) + ('const-wide/16 %s, 0x0' % reg if mr.group(2) == '-wide' else 'const/4 %s, 0x0' % reg)
                i += 1
                changed = True; patched += 1
                continue
        out.append(line); i += 1
    if changed: f.write_text('\n'.join(out))
print('patched call sites:', patched)
res = subprocess.run([str(java / 'java'), '-jar', str(r / 'tools/smali.jar'), 'assemble', str(stage), '-o', str(r / 'kyocera-compat.dex')], capture_output=True, text=True)
print('smali rc', res.returncode, res.stderr[-800:])
