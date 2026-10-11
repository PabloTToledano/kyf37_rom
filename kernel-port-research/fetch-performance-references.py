"""Fetch pinned primary-source references for the isolated performance work."""
from pathlib import Path
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

root = Path(__file__).resolve().parent / 'performance-reference'
root.mkdir(exist_ok=True)
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'KYF37-isolated-performance'}), timeout=60).read()
def resolve(tag):
    item = json.loads(get('https://api.github.com/repos/gregkh/linux/git/ref/tags/' + tag))['object']
    while item['type'] == 'tag':
        item = json.loads(get(item['url']))['object']
    return item['sha']
tags = {t: resolve(t) for t in ('v4.1.52', 'v3.18.140')}
jobs = [('zsmalloc.c', tags['v4.1.52'], 'mm/zsmalloc.c'),
        ('zsmalloc.h', tags['v4.1.52'], 'include/linux/zsmalloc.h'),
        ('zsmalloc-Kconfig', tags['v4.1.52'], 'mm/Kconfig'),
        ('workqueue.c', tags['v3.18.140'], 'kernel/workqueue.c'),
        ('workqueue.h', tags['v3.18.140'], 'include/linux/workqueue.h'),
        ('power-Kconfig', tags['v3.18.140'], 'kernel/power/Kconfig'),
        ('zram_drv.c', tags['v4.1.52'], 'drivers/block/zram/zram_drv.c')]
jobs += [(name.replace('/', '_'), tags['v3.18.140'], name) for name in
         ('drivers/power/power_supply_core.c', 'mm/vmstat.c', 'drivers/video/console/fbcon.c', 'block/genhd.c')]
def fetch(job):
    name, commit, path = job
    url = f'https://raw.githubusercontent.com/gregkh/linux/{commit}/{path}'
    data = (root / name).read_bytes() if (root / name).exists() else get(url)
    (root / name).write_bytes(data)
    return name, {'url': url, 'sha256': hashlib.sha256(data).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:
    files = dict(pool.map(fetch, jobs))
(root / 'provenance.json').write_text(json.dumps({'tags': tags, 'files': files}, indent=2) + '\n')
print(tags)
