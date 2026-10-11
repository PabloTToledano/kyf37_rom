"""Execute the actual stream-limit setter on ARM32 with context assertions."""
from pathlib import Path
import json
import subprocess

root = Path(__file__).resolve().parent
work = Path('/home/pablo/kyf37-kernel-port-research/backports')
test = work / 'host-tests/zram-context'
test.mkdir(parents=True, exist_ok=True)
zcomp = (work / 'kernel/drivers/staging/zram/zcomp.c').read_text()
a = zcomp.index('static bool zcomp_strm_multi_set_max_streams(')
b = zcomp.index('\nstatic void zcomp_strm_multi_destroy(', a)
setter = zcomp[a:b]
driver = (work / 'kernel/drivers/staging/zram/zram_drv.c').read_text()
a = driver.index('static int zram_bvec_write(')
b = driver.index('\nstatic int zram_bvec_rw(', a)
write = driver[a:b]
assert write.index('zs_unmap_object(meta->mem_pool, handle);') < write.index(
    'zcomp_strm_release(zram->comp, zstrm);')
harness = r'''
typedef _Bool bool;
#define true 1
struct list_head { struct list_head *next, *prev; };
#define LIST_HEAD(name) struct list_head name = {&name, &name}
#define list_entry(p,t,m) ((t *)((char *)(p) - __builtin_offsetof(t,m)))
#define list_for_each_entry_safe(p,n,h,m) for (p=list_entry((h)->next,__typeof__(*p),m), n=list_entry(p->m.next,__typeof__(*p),m); &p->m!=(h); p=n,n=list_entry(n->m.next,__typeof__(*n),m))
static int list_empty(const struct list_head *h) { return h->next == h; }
static void list_del(struct list_head *p) { p->prev->next=p->next; p->next->prev=p->prev; }
static void list_add(struct list_head *p, struct list_head *h) { p->next=h->next; p->prev=h; h->next->prev=p; h->next=p; }
static void list_move(struct list_head *p, struct list_head *h) { list_del(p); list_add(p,h); }
struct zcomp_strm { struct list_head list; int freed; };
struct zcomp_strm_multi { struct list_head idle_strm; int max_strm, avail_strm, strm_lock; };
struct zcomp { void *stream; };
static int held, frees, error;
static void spin_lock(int *p) { if (held) error=1; held=1; *p=1; }
static void spin_unlock(int *p) { if (!held) error=2; held=0; *p=0; }
static void zcomp_strm_free(struct zcomp *c, struct zcomp_strm *s) {
    (void)c;
    if (held) error=3; /* vmalloc-backed work memory must not be freed atomically */
    if (s->freed) error=4;
    s->freed=1; frees++;
}
''' + setter + r'''
static struct zcomp_strm nodes[4];
static int run_case(int available, int idle, int requested, int expected_freed, int expected_available) {
    struct zcomp_strm_multi zs;
    struct zcomp c = {&zs};
    int i;
    zs.idle_strm.next=zs.idle_strm.prev=&zs.idle_strm;
    zs.max_strm=4; zs.avail_strm=available; zs.strm_lock=0;
    held=frees=error=0;
    for (i=0; i<idle; ++i) { nodes[i].freed=0; list_add(&nodes[i].list,&zs.idle_strm); }
    if (!zcomp_strm_multi_set_max_streams(&c,requested)) return 10;
    if (error || held || frees!=expected_freed || zs.avail_strm!=expected_available || zs.max_strm!=requested) return 11;
    return 0;
}
void _start(void) {
    int rc=run_case(4,4,2,2,2);
    if (!rc) rc=run_case(4,4,8,0,4);
    if (!rc) rc=run_case(4,2,1,2,2); /* two streams still in use */
    if (!rc) rc=run_case(4,0,1,0,4);
    if (!rc) rc=run_case(1,1,1,0,1);
    register long r0 __asm__("r0")=rc;
    register long r7 __asm__("r7")=1;
    __asm__ volatile("svc 0" : "+r"(r0) : "r"(r7) : "memory");
    for (;;) {}
}
'''
(test / 'context.c').write_text(harness)
cross = '/home/pablo/kyf37-lineage/prebuilts/gcc/linux-x86/arm/arm-eabi-4.8/bin/arm-eabi-gcc'
binary = test / 'zram-context-arm-test'
subprocess.run([cross, '-O2', '-fno-strict-aliasing', '-fno-stack-protector', '-nostdlib',
                '-static', '-marm', '-march=armv7-a', '-Wl,-e,_start',
                str(test / 'context.c'), '-o', str(binary)], check=True)
subprocess.run([str(work / 'host-tools/qemu/usr/bin/qemu-arm'), '-cpu', 'cortex-a7',
                str(binary)], timeout=60, check=True)
report = {'ARM32_stream_limit_cases': 5, 'free_outside_spinlock_asserted': True,
          'allocator_mapping_released_before_stream_release': True,
          'physical_phone_access': False,
          'limit': 'Uses the actual setter with modeled list/lock/free primitives; not a kernel concurrency stress test.'}
(root / 'zram-context-test.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
