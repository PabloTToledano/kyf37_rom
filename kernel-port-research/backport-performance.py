"""Re-runnable performance/power changes in the independent kernel only."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
ref = root / 'performance-reference'
kernel = Path('/home/pablo/kyf37-kernel-port-research/backports/kernel')
assert kernel.resolve() == Path('/home/pablo/kyf37-kernel-port-research/backports/kernel')
provenance = json.loads((ref / 'provenance.json').read_text())
for name, meta in provenance['files'].items():
    assert hashlib.sha256((ref / name).read_bytes()).hexdigest() == meta['sha256'], name

def write(path, data):
    p = kernel / path
    if p.read_text() != data:
        p.write_text(data)
def replace(path, old, new):
    data = (kernel / path).read_text()
    if new in data:
        return
    assert data.count(old) == 1, (path, old)
    write(path, data.replace(old, new, 1))

# Stable 4.1 includes merged size classes and handle pinning needed to move
# objects during compaction. Preserve the original exported function signatures.
data = (ref / 'zsmalloc.c').read_text()
data = data.replace('#include <linux/zsmalloc.h>', '#include "zsmalloc.h"')
data = data.replace('#include <linux/zpool.h>', '#ifdef CONFIG_ZPOOL\n#include <linux/zpool.h>\n#endif')
data = data.replace('WRITE_ONCE(*(unsigned long *)handle, obj);',
                    'ACCESS_ONCE(*(unsigned long *)handle) = obj;')
data = data.replace('struct zs_pool *zs_create_pool(char *name, gfp_t flags)\n{',
                    'struct zs_pool *zs_create_pool(gfp_t flags)\n{\n\tchar *name = "kyf37-zram";')
# ZPOOL is intentionally unavailable in this vendor kernel; retain a compatible
# dead-code call rather than introducing another allocator subsystem.
data = data.replace('return zs_create_pool(name, gfp);', 'return zs_create_pool(gfp);')
# The ARM harness exposed a stable-4.1 livelock when a source zspage contains
# only a pinned object. It is repeatedly chosen without moving any bytes.
# Stop this class's pass on zero progress; a later explicit pass may retry.
old = '\twhile ((src_page = isolate_source_page(class))) {\n'
assert data.count(old) == 1
data = data.replace(old, old + '\t\tunsigned long migrated_start = nr_total_migrated;\n')
old = ('\t\tputback_zspage(pool, class, src_page);\n\t\tspin_unlock(&class->lock);\n'
       '\t\tnr_total_migrated += cc.nr_migrated;\n\t\tcond_resched();')
new = ('\t\tputback_zspage(pool, class, src_page);\n'
       '\t\tnr_total_migrated += cc.nr_migrated;\n'
       '\t\tif (nr_total_migrated == migrated_start) {\n'
       '\t\t\t/* Pinned source: avoid repeatedly selecting it. */\n'
       '\t\t\tsrc_page = NULL;\n\t\t\tbreak;\n\t\t}\n'
       '\t\tspin_unlock(&class->lock);\n\t\tcond_resched();')
assert data.count(old) == 1
data = data.replace(old, new)
marker = 'EXPORT_SYMBOL_GPL(zs_get_total_pages);'
assert data.count(marker) == 1
data = data.replace(marker, marker + '''

/* Original 3.10 ABI: report bytes, not pages, with 64-bit multiplication. */
u64 zs_get_total_size_bytes(struct zs_pool *pool)
{
    return (u64)zs_get_total_pages(pool) << PAGE_SHIFT;
}
EXPORT_SYMBOL_GPL(zs_get_total_size_bytes);
''')
write('drivers/staging/zsmalloc/zsmalloc-main.c', data)
header = (kernel / 'drivers/staging/zsmalloc/zsmalloc.h').read_text()
if 'unsigned long zs_compact(' not in header:
    header = header.replace('u64 zs_get_total_size_bytes(struct zs_pool *pool);',
        'u64 zs_get_total_size_bytes(struct zs_pool *pool);\n'
        'unsigned long zs_get_total_pages(struct zs_pool *pool);\n'
        'unsigned long zs_compact(struct zs_pool *pool);')
    write('drivers/staging/zsmalloc/zsmalloc.h', header)

# Expose explicit compaction without a polling daemon or permanent extra wakeups.
drv = 'drivers/staging/zram/zram_drv.c'
compact = '''static ssize_t compact_store(struct device *dev,
        struct device_attribute *attr, const char *buf, size_t len)
{
    struct zram *zram = dev_to_zram(dev);
    unsigned long value;
    int ret = kstrtoul(buf, 10, &value);

    if (ret)
        return ret;
    if (value != 1)
        return -EINVAL;
    down_read(&zram->init_lock);
    if (!init_done(zram)) {
        up_read(&zram->init_lock);
        return -EINVAL;
    }
    zs_compact(zram->meta->mem_pool);
    up_read(&zram->init_lock);
    return len;
}

'''
replace(drv, 'static ssize_t disksize_show(', compact + 'static ssize_t disksize_show(')
replace(drv, 'static DEVICE_ATTR(disksize,',
        'static DEVICE_ATTR(compact, 0200, NULL, compact_store);\nstatic DEVICE_ATTR(disksize,')
replace(drv, '\t&dev_attr_disksize.attr,', '\t&dev_attr_compact.attr,\n\t&dev_attr_disksize.attr,')

# Transplant only the stable power-efficient extension, not a new workqueue core.
wc = 'kernel/workqueue.c'
param = '''/* Opt-in unbound execution for work explicitly marked power efficient. */
#ifdef CONFIG_WQ_POWER_EFFICIENT_DEFAULT
static bool wq_power_efficient = true;
#else
static bool wq_power_efficient;
#endif
module_param_named(power_efficient, wq_power_efficient, bool, 0444);

'''
replace(wc, 'static bool wq_numa_enabled;', param + 'static bool wq_numa_enabled;')
replace('include/linux/workqueue.h', '\t__WQ_DRAINING\t\t= 1 << 16,',
        '\t/* Allows CPU affinity to be relaxed only for explicitly marked work. */\n'
        '\tWQ_POWER_EFFICIENT\t= 1 << 7,\n\n\t__WQ_DRAINING\t\t= 1 << 16,')
replace('include/linux/workqueue.h', 'extern struct workqueue_struct *system_freezable_wq;',
        'extern struct workqueue_struct *system_freezable_wq;\n'
        'extern struct workqueue_struct *system_power_efficient_wq;\n'
        'extern struct workqueue_struct *system_freezable_power_efficient_wq;')
replace(wc, 'EXPORT_SYMBOL_GPL(system_freezable_wq);',
        'EXPORT_SYMBOL_GPL(system_freezable_wq);\n'
        'struct workqueue_struct *system_power_efficient_wq __read_mostly;\n'
        'EXPORT_SYMBOL_GPL(system_power_efficient_wq);\n'
        'struct workqueue_struct *system_freezable_power_efficient_wq __read_mostly;\n'
        'EXPORT_SYMBOL_GPL(system_freezable_power_efficient_wq);')
replace(wc, '\t/* allocate wq and format name */',
        '\tif ((flags & WQ_POWER_EFFICIENT) && wq_power_efficient)\n'
        '\t\tflags |= WQ_UNBOUND;\n\n\t/* allocate wq and format name */')
replace(wc, '\tBUG_ON(!system_wq || !system_highpri_wq || !system_long_wq ||\n'
        '\t       !system_unbound_wq || !system_freezable_wq);',
        '\tsystem_power_efficient_wq = alloc_workqueue("events_power_efficient",\n'
        '\t\t\t\t\t      WQ_POWER_EFFICIENT, 0);\n'
        '\tsystem_freezable_power_efficient_wq =\n'
        '\t\talloc_workqueue("events_freezable_power_efficient",\n'
        '\t\t\t\tWQ_FREEZABLE | WQ_POWER_EFFICIENT, 0);\n'
        '\tBUG_ON(!system_wq || !system_highpri_wq || !system_long_wq ||\n'
        '\t       !system_unbound_wq || !system_freezable_wq ||\n'
        '\t       !system_power_efficient_wq || !system_freezable_power_efficient_wq);')
cfg = (ref / 'power-Kconfig').read_text()
a = cfg.index('config WQ_POWER_EFFICIENT_DEFAULT\n')
b = cfg.index('\nconfig ', a + 1)
path = 'kernel/power/Kconfig'
if 'config WQ_POWER_EFFICIENT_DEFAULT' not in (kernel / path).read_text():
    write(path, (kernel / path).read_text().rstrip() + '\n\n' + cfg[a:b].rstrip() + '\n')
write(path, (kernel / path).read_text().rstrip() + '\n')

# Same CPU-independent disk-event/cursor work selected in stable 3.18.
replace('drivers/video/console/fbcon.c', 'schedule_work(&info->queue);',
        'queue_work(system_power_efficient_wq, &info->queue);')
path = 'block/genhd.c'
data = (kernel / path).read_text()
if 'system_freezable_power_efficient_wq' not in data:
    assert data.count('system_freezable_wq') == 4
    write(path, data.replace('system_freezable_wq', 'system_freezable_power_efficient_wq'))
report = {'references': provenance['tags'],
          'features': ['stable 4.1 zsmalloc class merging and explicit compaction',
                       'stable 3.18 opt-in power-efficient workqueues'],
          'old_exported_allocator_signatures_preserved': True,
          'phone_access': False, 'hardware_tested': False}
(root / 'performance-implementation.json').write_text(json.dumps(report, indent=2) + '\n')
print(report)
