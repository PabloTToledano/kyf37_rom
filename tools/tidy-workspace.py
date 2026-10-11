"""Workspace tidy-up (2026-10-11). Dry run by default; --apply performs it.
 * DELETE only regenerable scratch (screenshots/intermediate APKs made while testing, font-sheet drafts, scrape temp files).
 * MOVE (never delete) superseded releases, old reports, stray research binaries, loose screenshots into archive/ and
   status/history markdown into docs/. Every move is recorded in archive/MANIFEST-20261011.tsv (src<TAB>dst) so it can be undone with
   python tools/tidy-workspace.py --undo.
 * Never touches: phone-backup/, kyf37-twrp-device/, third-party/*/site, tools/ venvs, .git, device-inspection scripts, current releases (v22, v23).
 * A move is skipped if a repo script mentions the file name (unless listed in FORCE) so build/flash tooling keeps working."""
import os, re, shutil, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
APPLY = '--apply' in sys.argv
UNDO = '--undo' in sys.argv
MANIFEST = 'archive/MANIFEST-20261011.tsv'

DELETE = (
    [f'kyf37-rom/{n}.png' for n in ('a', 'b', 'h', 'h1', 'h2', 't', 'w', 'w1', 'w2', 'o1', 'o2', 'o3', 'outer1', 'outer2', 'outer3')]
    + ['kyf37-rom/Kyf37Home-hide.apk', 'kyf37-rom/Kyf37Home-redesign.apk', 'kyf37-rom/Kyf37Home-shapes.apk',
       'kyf37-rom/s.so', 'kyf37-rom/libkyf37subdisplay.so']
    + glob.glob('device-inspection/outer-v2/fontwork/sheet*')
)

MOVES = []  # (src, dst)
def mv(pattern, dst):
    for p in sorted(glob.glob(pattern)):
        MOVES.append((p.replace('\\', '/'), dst))

# superseded releases and drafts
mv('kyf37-rom/android10-go-candidate-20261007-v19', 'archive/releases')
mv('kyf37-rom/android10-go-candidate-20261007-v20', 'archive/releases')
mv('kyf37-rom/kyf37-android10-go-20261007-twrp-v19.zip*', 'archive/releases')
mv('kyf37-rom/kyf37-android10-go-20261007-twrp-v20.zip*', 'archive/releases')
mv('kyf37-rom/superseded-*', 'archive/releases')
mv('kyf37-rom/vendor-recovery-*', 'archive/recovery-dumps')
mv('kyf37-rom/color-review', 'archive/screenshots')
# loose screenshots / captures
for pat in ('camera-test-*.png', 'camera2-photo-*.png', 'dev?.png', 'fb0_*.png', 'keitai-recovery-live.png', 'kirby-official-star.png', 'outer-screen-preview.png'):
    mv('kyf37-rom/' + pat, 'archive/screenshots')
# old per-version audit reports (current: v22, v23)
for v in ('v8', 'v9', 'v10', 'v18', 'v19', 'v20', 'v20-preliminary'):
    mv(f'kyf37-rom/android10-installed-vendor-symbol-audit-{v}.json', 'archive/reports')
# stray camera research binaries from the workspace root
for n in ('libmmcamera_interface.so', 'mm-qcamera-daemon.patched', 'runas_camera'):
    mv(n, 'archive/camera-research')
# status / history markdown -> docs
for n in ('ANDROID10-GO-CHECK', 'KEYPAD-SETTINGS-VISUAL', 'NATIVE-ABI-STATUS', 'OREO-BRINGUP', 'PORT-STATUS', 'RESOURCE-PORT-STATUS',
          'ROM-CANDIDATE-SUMMARY', 'SECONDARY-DISPLAY', 'STOCK-SOUND-PORT'):
    mv(f'kyf37-rom/{n}.md', 'docs/history')
for v in ('v18', 'v19', 'v20', 'v22', 'v23'):
    mv(f'kyf37-rom/RELEASE-{v}.md', 'docs/releases')
for n in ('CLEANUP-20261011', 'STATUS', 'KYF37-RECOVERY-PORT', 'ROOT-SETUP'):
    mv(f'device-inspection/{n}.md', 'docs/history' if n in ('CLEANUP-20261011', 'STATUS') else 'docs')
mv('kernel-port-research/*.md', 'docs/kernel')
mv('modem-investigation/*.md', 'docs/radio')

FORCE = set()

def corpus():
    parts = []
    for d in ('device-inspection', 'tools'):
        for base, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x not in ('stock-resource-venv', 'recovery-venv', 'node_modules', '__pycache__', 'scrcpy', 'fontwork')]
            for f in files:
                if f.endswith(('.py', '.sh', '.ps1')) and f != 'tidy-workspace.py':
                    try: parts.append(open(os.path.join(base, f), encoding='utf-8', errors='ignore').read())
                    except OSError: pass
    return '\n'.join(parts)

def undo():
    for line in open(MANIFEST, encoding='utf-8').read().splitlines():
        src, dst = line.split('\t')
        if os.path.exists(dst) and not os.path.exists(src):
            os.makedirs(os.path.dirname(src) or '.', exist_ok=True)
            shutil.move(dst, src); print('restored', src)

if UNDO:
    undo(); sys.exit(0)

blob = corpus()
plan, skipped = [], []
for src, dst in MOVES:
    name = os.path.basename(src)
    if name in blob and src not in FORCE:
        skipped.append((src, 'referenced by a script')); continue
    plan.append((src, dst))
log = []
for p in DELETE:
    if os.path.exists(p):
        print('DELETE', p)
        if APPLY: os.remove(p)
for src, dst in plan:
    print('MOVE  ', src, '->', dst)
    if APPLY:
        os.makedirs(dst, exist_ok=True)
        target = os.path.join(dst, os.path.basename(src))
        if os.path.exists(target):
            skipped.append((src, 'target exists')); continue
        shutil.move(src, target); log.append(f'{src}\t{target}')
for s, why in skipped:
    print('SKIP  ', s, '-', why)
if APPLY and log:
    os.makedirs('archive', exist_ok=True)
    with open(MANIFEST, 'a', encoding='utf-8') as f: f.write('\n'.join(log) + '\n')
print(('APPLIED' if APPLY else 'DRY RUN'), len(plan), 'moves,', len([p for p in DELETE if os.path.exists(p) or APPLY]), 'deletes,', len(skipped), 'skipped')
