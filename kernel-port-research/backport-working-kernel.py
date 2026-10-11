"""Re-runnable backports confined to the independent working-kernel snapshot."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parent
ref = root / 'backport-reference'
kernel = Path('/home/pablo/kyf37-kernel-port-research/backports/kernel')
assert kernel.resolve() == Path('/home/pablo/kyf37-kernel-port-research/backports/kernel')
assert 'PATCHLEVEL = 10' in (kernel / 'Makefile').read_text()
provenance = json.loads((ref / 'provenance.json').read_text())
for name, info in provenance['files'].items():
    assert hashlib.sha256((ref / name).read_bytes()).hexdigest() == info['sha256'], name

def write_if_changed(path, data):
    path = Path(path)
    encoded = data.encode() if isinstance(data, str) else data
    if not path.exists() or path.read_bytes() != encoded:
        path.write_bytes(encoded)

def replace(path, old, new):
    p = kernel / path
    text = p.read_text()
    if new in text:
        return
    assert text.count(old) == 1, (path, old)
    p.write_text(text.replace(old, new, 1))

def append(path, marker, data):
    p = kernel / path
    text = p.read_text()
    if marker not in text:
        p.write_text(text + '\n' + data)

if '"MemAvailable:' not in (kernel / 'fs/proc/meminfo.c').read_text():
    # The OEM tree has an extra 'allowed' local; retain its accounting and
    # transplant the upstream added calculation rather than fuzzing a patch.
    patch = (ref / 'memavailable.patch').read_text().split('diff --git a/fs/proc/meminfo.c', 1)[1]
    added = '\n'.join(line[1:] for line in patch.splitlines()
                      if line.startswith('+') and not line.startswith('+++'))
    a = added.index('\tfor_each_zone(zone)')
    b = added.index('\t\tavailable = 0;', a) + len('\t\tavailable = 0;')
    calculation = added[a:b] + '\n\n'
    replace('fs/proc/meminfo.c', '\tlong cached;',
            '\tlong cached;\n\tlong available;\n\tunsigned long pagecache;\n'
            '\tunsigned long wmark_low = 0;\n\tstruct zone *zone;')
    replace('fs/proc/meminfo.c', '\t/*\n\t * Tagged format, for easy grepping and expansion.',
            calculation + '\t/*\n\t * Tagged format, for easy grepping and expansion.')
    replace('fs/proc/meminfo.c', '\t\t"MemFree:        %8lu kB\\n"',
            '\t\t"MemFree:        %8lu kB\\n"\n\t\t"MemAvailable:   %8lu kB\\n"')
    replace('fs/proc/meminfo.c', '\t\tK(i.freeram),',
            '\t\tK(i.freeram),\n\t\tK(available),')

# The original algorithm subtracts watermarks. Signed arithmetic is explicit
# on ARM32 so low free memory cannot wrap into a huge availability estimate.
replace('fs/proc/meminfo.c', 'available = i.freeram - wmark_low;',
        'available = (long)i.freeram - (long)wmark_low;')

random_path = 'drivers/char/random.c'
if 'SYSCALL_DEFINE3(getrandom' not in (kernel / random_path).read_text():
    replace(random_path, '#include <linux/irq.h>',
            '#include <linux/irq.h>\n#include <linux/syscalls.h>')
    replace(random_path, 'static DECLARE_WAIT_QUEUE_HEAD(random_write_wait);',
            'static DECLARE_WAIT_QUEUE_HEAD(random_write_wait);\n'
            'static DECLARE_WAIT_QUEUE_HEAD(urandom_init_wait);')
    replace(random_path, '\t\tif (r->entropy_total > 128)\n\t\t\tr->initialized = 1;',
            '\t\tif (r->entropy_total > 128) {\n\t\t\tr->initialized = 1;\n'
            '\t\t\tif (r == &nonblocking_pool)\n'
            '\t\t\t\twake_up_interruptible(&urandom_init_wait);\n\t\t}\n')
    replace(random_path, '\t__u8 tmp[EXTRACT_SIZE];\n\n\ttrace_extract_entropy_user',
            '\t__u8 tmp[EXTRACT_SIZE];\n\tint large_request = (nbytes > 256);\n\n'
            '\ttrace_extract_entropy_user')
    text = (kernel / random_path).read_text()
    start = text.index('static ssize_t extract_entropy_user')
    end = text.index('EXPORT_SYMBOL(get_random_bytes);', start)
    section = text[start:end]
    if 'if (large_request && need_resched())' not in section:
        assert section.count('if (need_resched())') == 1
        section = section.replace('if (need_resched())', 'if (large_request && need_resched())')
    (kernel / random_path).write_text(text[:start] + section + text[end:])
    replace(random_path,
            '\nrandom_read(struct file *file, char __user *buf, size_t nbytes, loff_t *ppos)',
            '\n_random_read(int nonblock, char __user *buf, size_t nbytes)')
    replace(random_path, 'if (file->f_flags & O_NONBLOCK)', 'if (nonblock)')
    replace(random_path, 'static ssize_t\nurandom_read(',
            'static ssize_t\nrandom_read(struct file *file, char __user *buf, size_t nbytes, loff_t *ppos)\n'
            '{\n\treturn _random_read(file->f_flags & O_NONBLOCK, buf, nbytes);\n}\n\n'
            'static ssize_t\nurandom_read(')
    upstream = (ref / random_path).read_text()
    start = upstream.index('SYSCALL_DEFINE3(getrandom')
    end = upstream.index('\n/***************************************************************', start)
    append(random_path, 'SYSCALL_DEFINE3(getrandom', upstream[start:end] + '\n')
    replace('include/linux/syscalls.h', '\nasmlinkage long sys_finit_module(int fd, const char __user *uargs, int flags);',
            '\nasmlinkage long sys_finit_module(int fd, const char __user *uargs, int flags);\n'
            'asmlinkage long sys_getrandom(char __user *buf, size_t count, unsigned int flags);')
    replace('include/uapi/linux/random.h', '#endif /* _UAPI_LINUX_RANDOM_H */',
            '#define GRND_NONBLOCK 0x0001\n#define GRND_RANDOM 0x0002\n\n'
            '#endif /* _UAPI_LINUX_RANDOM_H */')
    replace('arch/arm/include/uapi/asm/unistd.h',
            '#define __NR_sched_getattr\t\t(__NR_SYSCALL_BASE+381)',
            '#define __NR_sched_getattr\t\t(__NR_SYSCALL_BASE+381)\n'
            '#define __NR_getrandom\t\t\t(__NR_SYSCALL_BASE+384)')
    replace('arch/arm/include/asm/unistd.h', '#define __NR_syscalls  (384)',
            '#define __NR_syscalls  (388)')
    replace('arch/arm/kernel/calls.S', '\t\tCALL(sys_sched_getattr)\n',
            '\t\tCALL(sys_sched_getattr)\n'
            '\t\tCALL(sys_ni_syscall)\t/* 382: renameat2 not backported */\n'
            '\t\tCALL(sys_ni_syscall)\t/* 383: seccomp syscall not backported */\n'
            '/* 384 */\tCALL(sys_getrandom)\n')

p = kernel / random_path
write_if_changed(p, p.read_text().rstrip() + '\n')
# ARM's legacy table pads to a multiple of four and verifies that padded size.
p = kernel / 'arch/arm/include/asm/unistd.h'
write_if_changed(p, p.read_text().replace('#define __NR_syscalls  (385)', '#define __NR_syscalls  (388)'))

# LZ4 codec is copied from the pinned stable source; retain its licensing.
for name in ['include/linux/lz4.h', 'lib/lz4/Makefile', 'lib/lz4/lz4_compress.c',
             'lib/lz4/lz4_decompress.c', 'lib/lz4/lz4defs.h']:
    dest = kernel / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_if_changed(dest, (ref / name).read_bytes())
append('lib/Kconfig', 'config LZ4_COMPRESS',
       'config LZ4_COMPRESS\n\ttristate\n\nconfig LZ4_DECOMPRESS\n\ttristate\n')
append('lib/Makefile', 'obj-$(CONFIG_LZ4_COMPRESS)',
       'obj-$(CONFIG_LZ4_COMPRESS) += lz4/\nobj-$(CONFIG_LZ4_DECOMPRESS) += lz4/\n')

compat = '''/* Compatibility with the original KYF37 3.10 allocator/API. */
#ifndef _KYF37_ZRAM_COMPAT_H
#define _KYF37_ZRAM_COMPAT_H
#include <linux/slab.h>
#include <linux/vmalloc.h>
#include "../zsmalloc/zsmalloc.h"
static inline void kyf37_kvfree(const void *p)
{
    if (is_vmalloc_addr(p))
        vfree(p);
    else
        kfree(p);
}
static inline unsigned long kyf37_zs_get_total_pages(struct zs_pool *pool)
{
    return zs_get_total_size_bytes(pool) >> PAGE_SHIFT;
}
#endif
'''
write_if_changed(kernel / 'drivers/staging/zram/kyf37_compat.h', compat)
for src in sorted((ref / 'drivers/block/zram').iterdir()):
    if not src.is_file():
        continue
    data = src.read_text()
    if src.suffix in ('.c', '.h'):
        data = data.replace('#include <linux/zsmalloc.h>', '#include "../zsmalloc/zsmalloc.h"')
        data = data.replace('kvfree(', 'kyf37_kvfree(')
        if 'kyf37_kvfree(' in data or 'zs_get_total_pages(' in data:
            # Include after kernel headers, before the first project header.
            first = re.search(r'^#include "', data, re.M)
            assert first is not None, src
            data = data[:first.start()] + '#include "kyf37_compat.h"\n' + data[first.start():]
        data = data.replace('zs_get_total_pages(', 'kyf37_zs_get_total_pages(')
    if src.name == 'zram_drv.c':
        data = data.replace('bio->bi_iter.bi_sector', 'bio->bi_sector')
        data = data.replace('bio->bi_iter.bi_size', 'bio->bi_size')
        data = data.replace('struct bio_vec bvec;\n\tstruct bvec_iter iter;',
                            'struct bio_vec *bvec;\n\tint iter;')
        # 3.10 iterates bio_vec pointers; later kernels iterate values.
        a = data.index('static void __zram_make_request(')
        b = data.index('\nstatic void zram_make_request(', a)
        part = data[a:b].replace('bvec.bv_', 'bvec->bv_').replace('&bvec,', 'bvec,').replace('&bvec)', 'bvec)')
        data = data[:a] + part + data[b:]
        # Original zsmalloc mappings disable preemption. A multi-stream
        # release can free vmalloc-backed work memory after a limit reduction;
        # restore the mapping/preemption state before releasing that stream.
        old = ('\tzcomp_strm_release(zram->comp, zstrm);\n\tlocked = false;\n'
               '\tzs_unmap_object(meta->mem_pool, handle);')
        new = ('\tzs_unmap_object(meta->mem_pool, handle);\n'
               '\tzcomp_strm_release(zram->comp, zstrm);\n\tlocked = false;')
        assert data.count(old) == 1
        data = data.replace(old, new)
    if src.name == 'zcomp.c':
        a = data.index('static bool zcomp_strm_multi_set_max_streams(')
        b = data.index('\nstatic void zcomp_strm_multi_destroy(', a)
        data = data[:a] + '''static bool zcomp_strm_multi_set_max_streams(struct zcomp *comp, int num_strm)
{
    struct zcomp_strm_multi *zs = comp->stream;
    struct zcomp_strm *zstrm, *next;
    LIST_HEAD(to_free);

    spin_lock(&zs->strm_lock);
    zs->max_strm = num_strm;
    while (zs->avail_strm > num_strm && !list_empty(&zs->idle_strm)) {
        zstrm = list_entry(zs->idle_strm.next, struct zcomp_strm, list);
        list_move(&zstrm->list, &to_free);
        zs->avail_strm--;
    }
    spin_unlock(&zs->strm_lock);

    /* kvfree may sleep for vmalloc-backed compression working memory. */
    list_for_each_entry_safe(zstrm, next, &to_free, list) {
        list_del(&zstrm->list);
        zcomp_strm_free(comp, zstrm);
    }
    return true;
}
''' + data[b:]
    write_if_changed(kernel / 'drivers/staging/zram' / src.name, data)
write_if_changed(kernel / 'drivers/staging/zram/zram.txt',
                 (ref / 'Documentation/blockdev/zram.txt').read_bytes())

report = {'kernel': str(kernel), 'reference_commit': provenance['stable_commit'],
          'features': ['MemAvailable with signed watermark subtraction',
                       'ARM EABI getrandom syscall 384 with initialization wait',
                       'stable 3.18 zram with LZ4, multiple streams, limits and statistics'],
          'compatibility': ['original zsmalloc ABI retained', '3.10 bio iterator adapted',
                            'compression streams freed outside spinlocks and allocator mappings'],
          'hardware_tested': False, 'physical_phone_access_forbidden': True}
(root / 'backport-implementation.json').write_text(json.dumps(report, indent=2) + '\n')
print('Applied isolated backports:', report['features'])
