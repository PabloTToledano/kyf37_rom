"""Download primary-source Linux references with pinned identities and hashes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import urllib.request

root = Path(__file__).resolve().parent / 'backport-reference'
root.mkdir(exist_ok=True)
headers = {'User-Agent': 'KYF37-kernel-backports'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60).read()
ref = json.loads(get('https://api.github.com/repos/gregkh/linux/git/ref/tags/v3.18.140'))['object']
while ref['type'] == 'tag':
    ref = json.loads(get(ref['url']))['object']
commit = ref['sha']
paths = ['drivers/block/zram/' + name for name in
         ['zram_drv.c', 'zram_drv.h', 'zcomp.c', 'zcomp.h', 'zcomp_lzo.c',
          'zcomp_lzo.h', 'zcomp_lz4.c', 'zcomp_lz4.h', 'Kconfig', 'Makefile']]
paths += ['include/linux/zsmalloc.h', 'mm/zsmalloc.c', 'drivers/char/random.c',
          'include/uapi/linux/random.h', 'arch/arm/include/uapi/asm/unistd.h',
          'arch/arm/kernel/calls.S', 'Documentation/blockdev/zram.txt']
paths += ['include/linux/lz4.h', 'lib/lz4/Makefile', 'lib/lz4/lz4_compress.c',
          'lib/lz4/lz4_decompress.c', 'lib/lz4/lz4defs.h']
jobs = [(p, f'https://raw.githubusercontent.com/gregkh/linux/{commit}/{p}') for p in paths]
jobs += [(short + '.patch', 'https://github.com/torvalds/linux/commit/' + sha + '.patch')
         for short, sha in [('memavailable', '34e431b0ae398fc54ea69ff85ec700722c9da773'),
                            ('getrandom', 'c6e9d6f38894798696f23c8084ca7edbf16ee895')]]
def fetch(job):
    name, url = job
    p = root / name
    data = p.read_bytes() if p.exists() else get(url)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return name, {'url': url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
with ThreadPoolExecutor(max_workers=4) as pool:
    files = dict(pool.map(fetch, jobs))
(root / 'provenance.json').write_text(json.dumps({'stable_commit': commit,
    'tag': 'v3.18.140', 'files': files}, indent=2) + '\n')
print('Pinned', commit, 'downloaded', len(files), 'reference files')
